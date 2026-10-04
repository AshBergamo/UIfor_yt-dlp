package com.aipytorch.baixarmusicayoutube;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

/** Pure Java URL policy. Rules are loaded from the shared sources.json asset. */
public final class SourcePolicy {
    public static final class Rule {
        final String[] hosts;
        final boolean subdomains, shortLink;
        final Pattern path;
        public Rule(String[] hosts, boolean subdomains, String path, boolean shortLink) {
            this.hosts = hosts;
            this.subdomains = subdomains;
            this.path = Pattern.compile(path);
            this.shortLink = shortLink;
        }
    }
    public static final class Source {
        public final String id, name;
        public final boolean experimental;
        public final List<Rule> rules;
        public final List<String> extractors;
        public Source(String id, String name, boolean experimental, List<Rule> rules, List<String> extractors) {
            this.id = id; this.name = name; this.experimental = experimental;
            this.rules = rules; this.extractors = extractors;
        }
    }
    public static final class Match {
        public final Source source;
        public final String url;
        public final boolean shortLink;
        Match(Source source, String url, boolean shortLink) {
            this.source = source; this.url = url; this.shortLink = shortLink;
        }
    }
    private final List<Source> sources;
    public SourcePolicy(List<Source> sources) { this.sources = sources; }
    public static String normalize(String input) {
        String value = input == null ? "" : input.trim();
        return !value.isEmpty() && !value.contains("://") ? "https://" + value : value;
    }
    public Match classify(String input) {
        try {
            String url = normalize(input);
            URI uri = URI.create(url);
            if (!("https".equalsIgnoreCase(uri.getScheme()) || "http".equalsIgnoreCase(uri.getScheme()))
                    || uri.getHost() == null || uri.getRawUserInfo() != null
                    || (uri.getPort() != -1 && uri.getPort() != 80 && uri.getPort() != 443)) return null;
            String host = uri.getHost().toLowerCase(Locale.ROOT).replaceAll("\\.$", "");
            String path = uri.getRawPath();
            if (path == null || path.isEmpty()) path = "/";
            for (Source source : sources) for (Rule rule : source.rules) for (String domain : rule.hosts) {
                if ((host.equals(domain) || rule.subdomains && host.endsWith("." + domain))
                        && rule.path.matcher(path).matches()) {
                    String prefix = uri.getScheme().toLowerCase(Locale.ROOT) + "://" + uri.getRawAuthority().toLowerCase(Locale.ROOT);
                    String normalized = prefix + url.substring(url.indexOf("://") + 3 + uri.getRawAuthority().length());
                    return new Match(source, normalized, rule.shortLink);
                }
            }
        } catch (IllegalArgumentException ignored) { }
        return null;
    }
    public String help() {
        List<String> names = new ArrayList<>();
        for (boolean experimental : new boolean[]{false, true}) for (Source source : sources)
            if (source.experimental == experimental) names.add(source.name + (experimental ? " (experimental)" : ""));
        return String.join(" · ", names);
    }
    public String extractors() {
        List<String> names = new ArrayList<>();
        for (Source source : sources) names.addAll(source.extractors);
        return String.join(",", names);
    }
    public static boolean finalOutput(String name, String format) {
        String lower = name.toLowerCase(Locale.ROOT);
        return lower.endsWith("." + format) && !lower.contains(".temp.") && !lower.contains(".part.");
    }
    public static String friendlyError(String detail, String sourceName) {
        String low = detail.toLowerCase(Locale.ROOT);
        String message;
        if (low.contains("login required") || low.contains("log in") || low.contains("sign in")
                || low.contains("cookies") || low.contains("private video"))
            message = sourceName + " exige uma sessão ou o conteúdo é restrito. Tente um vídeo público acessível sem login.";
        else if (low.contains("geo") || low.contains("your country") || low.contains("your region"))
            message = "Esse conteúdo não está disponível nesta região.";
        else if (low.contains("429") || low.contains("rate limit") || low.contains("too many requests"))
            message = "A fonte limitou as consultas. Aguarde um pouco e tente novamente.";
        else if (low.contains("requested format"))
            message = "Não há mídia compatível com o formato escolhido. Para extrair áudio, o vídeo precisa ter áudio.";
        else if (low.contains("audio codec") || low.contains("no audio"))
            message = "Esse vídeo não possui uma faixa de áudio que possa ser extraída para MP3/WAV.";
        else if (low.contains("removed") || low.contains("unavailable") || low.contains("not found"))
            message = "O vídeo foi removido, está restrito ou não está disponível.";
        else message = "Não foi possível obter a mídia de " + sourceName + ". O link ou o extrator pode precisar de atualização.";
        String diagnostic = detail.replaceAll("https?://\\S+", "[endereço omitido]");
        return message + "\n\nDetalhe: " + diagnostic.substring(0, Math.min(500, diagnostic.length()));
    }
}
