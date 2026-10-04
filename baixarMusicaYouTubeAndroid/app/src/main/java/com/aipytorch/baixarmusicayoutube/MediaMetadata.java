package com.aipytorch.baixarmusicayoutube;

import android.content.Context;
import com.yausername.ffmpeg.FFmpeg;
import com.yausername.youtubedl_android.YoutubeDL;
import com.yausername.youtubedl_android.YoutubeDLRequest;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

/** Optional metadata, separate from downloads, with a cancellable process ID. */
final class MediaMetadata {
    interface Status { void show(String message); }
    private static boolean ready, updated;

    static synchronized void prepare(Context context, Status status) throws Exception {
        if (!ready) {
            if (status != null) status.show("Inicializando yt-dlp e FFmpeg…");
            YoutubeDL.getInstance().init(context);
            FFmpeg.getInstance().init(context);
            ready = true;
        }
        if (!updated) {
            if (status != null) status.show("Atualizando yt-dlp…");
            try { YoutubeDL.getInstance().updateYoutubeDL(context, YoutubeDL.UpdateChannel._STABLE); }
            catch (Exception ignored) { if (status != null) status.show("Usando yt-dlp empacotado…"); }
            updated = true;
        }
    }

    static SourcePolicy loadPolicy(Context context) throws Exception {
        ByteArrayOutputStream data = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open("sources.json")) {
            byte[] buffer = new byte[4096]; int read;
            while ((read = input.read(buffer)) != -1) data.write(buffer, 0, read);
        }
        JSONArray catalog = new JSONObject(data.toString("UTF-8")).getJSONArray("sources");
        List<SourcePolicy.Source> sources = new ArrayList<>();
        for (int n = 0; n < catalog.length(); n++) {
            JSONObject source = catalog.getJSONObject(n);
            List<SourcePolicy.Rule> rules = new ArrayList<>();
            JSONArray rawRules = source.getJSONArray("rules");
            for (int k = 0; k < rawRules.length(); k++) {
                JSONObject rule = rawRules.getJSONObject(k);
                JSONArray rawHosts = rule.getJSONArray("hosts");
                String[] hosts = new String[rawHosts.length()];
                for (int h = 0; h < hosts.length; h++) hosts[h] = rawHosts.getString(h);
                rules.add(new SourcePolicy.Rule(hosts, rule.optBoolean("subdomains"), rule.getString("path"), rule.optBoolean("short")));
            }
            List<String> extractors = new ArrayList<>();
            JSONArray rawExtractors = source.getJSONArray("extractors");
            for (int k = 0; k < rawExtractors.length(); k++) extractors.add(rawExtractors.getString(k));
            sources.add(new SourcePolicy.Source(source.getString("id"), source.getString("name"), source.optBoolean("experimental"), rules, extractors));
        }
        return new SourcePolicy(sources);
    }

    static final class Post {
        final String url;
        final List<JSONObject> videos;
        Post(String url, List<JSONObject> videos) { this.url = url; this.videos = videos; }
    }

    static final class Job {
        final String processId = "metadata-" + java.util.UUID.randomUUID();
        private volatile boolean cancelled;
        private volatile HttpURLConnection connection;
        void cancel() {
            cancelled = true;
            HttpURLConnection active = connection;
            if (active != null) active.disconnect();
            YoutubeDL.getInstance().destroyProcessById(processId);
        }
        void check() throws InterruptedException {
            if (cancelled || Thread.currentThread().isInterrupted()) throw new InterruptedException("Consulta cancelada.");
        }
        String resolve(String input, SourcePolicy policy) throws Exception {
            String url = input;
            for (int attempt = 0; attempt < 6; attempt++) {
                check();
                SourcePolicy.Match match = policy.classify(url);
                if (match == null) throw new IllegalArgumentException("Use um link de vídeo de uma das fontes aceitas.");
                if (!match.shortLink) return match.url;
                if (attempt == 5) break;
                HttpURLConnection active = (HttpURLConnection) new URL(url).openConnection();
                connection = active;
                try {
                    active.setInstanceFollowRedirects(false);
                    active.setConnectTimeout(5000); active.setReadTimeout(5000);
                    active.setRequestProperty("User-Agent", "Mozilla/5.0");
                    active.setRequestProperty("Range", "bytes=0-0");
                    int code = active.getResponseCode();
                    String location = active.getHeaderField("Location");
                    if (code < 300 || code >= 400 || location == null)
                        throw new IllegalArgumentException("Não foi possível resolver o link compartilhado. Cole o endereço da página do vídeo.");
                    url = new URL(new URL(url), location).toString();
                } finally { active.disconnect(); connection = null; }
            }
            throw new IllegalArgumentException("O link compartilhado tem redirecionamentos demais.");
        }
        Post lookup(Context context, SourcePolicy policy, String input, Status status) throws Exception {
            check();
            prepare(context, status);
            check();
            String url = resolve(input, policy);
            YoutubeDLRequest request = new YoutubeDLRequest(url);
            request.addOption("--simulate"); request.addOption("--no-playlist");
            request.addOption("--no-cache-dir"); request.addOption("--no-warnings");
            request.addOption("--socket-timeout", status == null ? "5" : "10");
            request.addOption("--retries", "0"); request.addOption("--extractor-retries", "0");
            request.addOption("--use-extractors", policy.extractors());
            request.addOption("--print", "{\"index\":%(playlist_index|1)j,\"id\":%(id)j,\"title\":%(title)j,\"thumbnail\":%(thumbnail)j,\"duration\":%(duration)j,\"live\":%(is_live)j,\"live_status\":%(live_status)j}");
            try {
                check();
                String output = YoutubeDL.getInstance().execute(request, processId, false, null).getOut();
                check();
                if (output.length() > 1024 * 1024) throw new IllegalArgumentException("A resposta de metadados excedeu o limite.");
                List<JSONObject> videos = new ArrayList<>();
                for (String line : output.split("\r?\n")) {
                    if (!line.trim().startsWith("{")) continue;
                    JSONObject video = new JSONObject(line);
                    if (video.optBoolean("live") || video.optString("live_status").equals("is_upcoming"))
                        throw new IllegalArgumentException("Use um vídeo gravado ou clip; transmissões ao vivo ficam para outra etapa.");
                    video.put("index", video.optInt("index", videos.size() + 1));
                    if (video.isNull("title")) video.put("title", "Vídeo " + (videos.size() + 1));
                    videos.add(video);
                }
                if (videos.isEmpty()) throw new IllegalArgumentException("Nenhum vídeo disponível nesse post.");
                return new Post(url, videos);
            } finally { YoutubeDL.getInstance().destroyProcessById(processId); }
        }
    }
}
