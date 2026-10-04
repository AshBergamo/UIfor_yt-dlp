package com.aipytorch.baixarmusicayoutube;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.yausername.ffmpeg.FFmpeg;
import com.yausername.youtubedl_android.YoutubeDL;
import com.yausername.youtubedl_android.YoutubeDLRequest;

import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import kotlin.Unit;

public class MainActivity extends Activity {
    private static final int COR_FUNDO = Color.rgb(15, 17, 21);
    private static final int COR_CARD = Color.rgb(26, 29, 35);
    private static final int COR_INPUT = Color.rgb(11, 13, 18);
    private static final int COR_BORDA = Color.rgb(45, 49, 57);
    private static final int COR_TEXTO = Color.rgb(232, 234, 237);
    private static final int COR_TEXTO_SUAVE = Color.rgb(139, 145, 154);
    private static final int COR_VERMELHO = Color.rgb(255, 31, 45);
    private static final int COR_VERMELHO_ESCURO = Color.rgb(200, 16, 31);
    private static final int DURACAO_MAXIMA_GIF = 30;
    private static final String FILTRO_GIF =
            "fps=15,scale=w='min(720,iw)':h=-2:flags=lanczos,"
                    + "split[quadros][paleta];"
                    + "[paleta]palettegen=max_colors=256:stats_mode=diff[cores];"
                    + "[quadros][cores]paletteuse=dither=sierra2_4a:diff_mode=rectangle";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private EditText inputUrl;
    private Spinner spinnerFormato;
    private EditText inputGifInicio;
    private EditText inputGifFim;
    private TextView gifLabel;
    private LinearLayout gifBox;
    private CheckBox checkPlaylist;
    private Button buttonDownload;
    private ProgressBar progressBar;
    private TextView statusText;
    private volatile boolean backendReady = false;

    private final String[] labels = {
            "MP4 (Vídeo)",
            "MP3 (Áudio)",
            "WEBM (Vídeo) - Formato Web",
            "MKV (Vídeo)",
            "GIF (Animação)",
            "WAV (Áudio)"
    };

    private final String[] values = {"mp4", "mp3", "webm", "mkv", "gif", "wav"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
    }

    private void buildUi() {
        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(COR_FUNDO);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setMinimumHeight(getResources().getDisplayMetrics().heightPixels - dp(42));
        root.setPadding(dp(22), dp(26), dp(22), dp(26));
        scrollView.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(2), 0, dp(2), 0);
        root.addView(header, fullWidth());

        TextView title = new TextView(this);
        title.setText("YouTube Downloader");
        title.setTextColor(COR_TEXTO);
        title.setTextSize(24);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setIncludeFontPadding(false);
        header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));

        TextView version = new TextView(this);
        version.setText("v3");
        version.setTextColor(COR_VERMELHO);
        version.setTextSize(13);
        version.setGravity(Gravity.CENTER);
        version.setIncludeFontPadding(false);
        version.setPadding(dp(12), dp(7), dp(12), dp(7));
        version.setBackground(rounded(Color.rgb(58, 16, 21), dp(10), 0, 0));
        header.addView(version);

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20), dp(22), dp(20), dp(22));
        card.setBackground(rounded(COR_CARD, dp(18), COR_BORDA, 1));
        LinearLayout.LayoutParams cardParams = fullWidth();
        cardParams.setMargins(0, dp(22), 0, 0);
        root.addView(card, cardParams);

        inputUrl = input("Cole aqui o link do vídeo do YouTube...");
        card.addView(label("Link do Vídeo"));
        card.addView(inputUrl, withBottomMargin(fullWidthHeight(dp(48)), dp(14)));

        spinnerFormato = new Spinner(this);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
                this,
                android.R.layout.simple_spinner_item,
                labels
        );
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerFormato.setAdapter(adapter);
        spinnerFormato.setPadding(dp(10), 0, dp(42), 0);
        spinnerFormato.setBackgroundColor(Color.TRANSPARENT);
        spinnerFormato.setPopupBackgroundDrawable(rounded(COR_CARD, dp(12), COR_BORDA, 1));

        FrameLayout formatBox = new FrameLayout(this);
        formatBox.setBackground(rounded(COR_INPUT, dp(10), COR_BORDA, 1));
        formatBox.setClickable(true);
        formatBox.setOnClickListener(view -> spinnerFormato.performClick());
        formatBox.addView(spinnerFormato, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        TextView formatArrow = new TextView(this);
        formatArrow.setText("\u25BE");
        formatArrow.setTextColor(COR_TEXTO_SUAVE);
        formatArrow.setTextSize(13);
        formatArrow.setGravity(Gravity.CENTER);
        formatArrow.setIncludeFontPadding(false);
        formatArrow.setClickable(false);
        FrameLayout.LayoutParams arrowParams = new FrameLayout.LayoutParams(dp(34), dp(34));
        arrowParams.gravity = Gravity.END | Gravity.CENTER_VERTICAL;
        arrowParams.setMargins(0, 0, dp(8), 0);
        formatBox.addView(formatArrow, arrowParams);
        card.addView(label("Formato de Saída"));
        card.addView(formatBox, withBottomMargin(fullWidthHeight(dp(54)), dp(14)));

        gifBox = new LinearLayout(this);
        gifBox.setOrientation(LinearLayout.HORIZONTAL);
        inputGifInicio = input("Ex.: 00:10");
        inputGifFim = input("Ex.: 00:20");
        LinearLayout.LayoutParams halfA = new LinearLayout.LayoutParams(0, dp(50), 1);
        halfA.setMargins(0, 0, dp(8), 0);
        LinearLayout.LayoutParams halfB = new LinearLayout.LayoutParams(0, dp(50), 1);
        halfB.setMargins(dp(8), 0, 0, 0);
        gifBox.addView(inputGifInicio, halfA);
        gifBox.addView(inputGifFim, halfB);
        gifLabel = label("Intervalo do GIF");
        card.addView(gifLabel);
        card.addView(gifBox, withBottomMargin(fullWidth(), dp(14)));

        checkPlaylist = new CheckBox(this);
        checkPlaylist.setText("Baixar playlist inteira quando o link tiver playlist");
        checkPlaylist.setTextColor(COR_TEXTO_SUAVE);
        checkPlaylist.setTextSize(13);
        checkPlaylist.setButtonTintList(android.content.res.ColorStateList.valueOf(COR_TEXTO_SUAVE));
        card.addView(checkPlaylist, withBottomMargin(fullWidth(), dp(16)));

        buttonDownload = new Button(this);
        buttonDownload.setText("Baixar Vídeo");
        buttonDownload.setTextColor(Color.WHITE);
        buttonDownload.setTextSize(15);
        buttonDownload.setAllCaps(false);
        buttonDownload.setBackground(rounded(COR_VERMELHO, dp(12), COR_VERMELHO_ESCURO, 1));
        card.addView(buttonDownload, withBottomMargin(fullWidthHeight(dp(54)), dp(20)));

        TextView progressTitle = label("Progresso");
        progressTitle.setGravity(Gravity.CENTER);
        card.addView(progressTitle);

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setProgress(0);
        progressBar.setProgressDrawable(roundedProgressDrawable());
        card.addView(progressBar, withBottomMargin(fullWidthHeight(dp(10)), dp(14)));

        statusText = new TextView(this);
        statusText.setText("Aguardando...");
        statusText.setTextColor(COR_TEXTO_SUAVE);
        statusText.setTextSize(13);
        statusText.setGravity(Gravity.CENTER);
        card.addView(statusText, fullWidth());

        TextView footer = new TextView(this);
        footer.setText("Licença GPLv3\nDesenvolvido principalmente com Inteligência Artificial\nV 3");
        footer.setTextColor(COR_TEXTO_SUAVE);
        footer.setGravity(Gravity.CENTER);
        footer.setTextSize(12);
        footer.setAlpha(0.82f);
        LinearLayout.LayoutParams footerParams = fullWidth();
        footerParams.setMargins(0, dp(22), 0, 0);
        root.addView(footer, footerParams);

        spinnerFormato.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                updateFormatUi();
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
            }
        });
        buttonDownload.setOnClickListener(view -> startDownload());
        updateFormatUi();
        setContentView(scrollView);
    }

    private TextView label(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(COR_TEXTO);
        view.setTextSize(14);
        view.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        view.setIncludeFontPadding(false);
        view.setPadding(0, 0, 0, dp(9));
        return view;
    }

    private EditText input(String hint) {
        EditText view = new EditText(this);
        view.setHint(hint);
        view.setHintTextColor(Color.rgb(90, 95, 106));
        view.setTextColor(COR_TEXTO);
        view.setTextSize(14);
        view.setSingleLine(true);
        view.setInputType(InputType.TYPE_CLASS_TEXT);
        view.setPadding(dp(14), 0, dp(14), 0);
        view.setBackground(rounded(COR_INPUT, dp(10), COR_BORDA, 1));
        return view;
    }

    private void updateFormatUi() {
        String format = selectedFormat();
        boolean gif = "gif".equals(format);
        gifLabel.setVisibility(gif ? View.VISIBLE : View.GONE);
        gifBox.setVisibility(gif ? View.VISIBLE : View.GONE);
        if ("gif".equals(format)) {
            buttonDownload.setText("Gerar GIF");
        } else if ("mp3".equals(format) || "wav".equals(format)) {
            buttonDownload.setText("Baixar Áudio");
        } else {
            buttonDownload.setText("Baixar Vídeo");
        }
    }

    private String selectedFormat() {
        int position = spinnerFormato.getSelectedItemPosition();
        if (position < 0 || position >= values.length) {
            return "mp4";
        }
        return values[position];
    }

    private void startDownload() {
        String url = normalizeUrl(inputUrl.getText().toString());
        if (!isYoutubeUrl(url)) {
            toast("URL inválida. Informe um link válido do YouTube.");
            return;
        }

        String format = selectedFormat();
        Double gifStart = null;
        Double gifEnd = null;
        if ("gif".equals(format)) {
            try {
                gifStart = parseSeconds(inputGifInicio.getText().toString(), "inicial");
                gifEnd = parseSeconds(inputGifFim.getText().toString(), "final");
                validateGifRange(gifStart, gifEnd);
            } catch (IllegalArgumentException ex) {
                toast(ex.getMessage());
                return;
            }
        }

        setWorking(true, "Preparando...");
        File workDir = new File(getCacheDir(), "yt_download_work");
        Double finalGifStart = gifStart;
        Double finalGifEnd = gifEnd;

        executor.execute(() -> {
            int savedCount = 0;
            try {
                ensureDownloaderReady();
                updateYtDlpIfPossible();

                deleteTree(workDir);
                workDir.mkdirs();

                YoutubeDLRequest request = buildRequest(
                        url,
                        format,
                        workDir,
                        checkPlaylist.isChecked(),
                        finalGifStart,
                        finalGifEnd
                );

                updateStatus("Baixando...", true);
                String processId = "download-" + System.currentTimeMillis();
                YoutubeDL.getInstance().execute(request, processId, true, (progress, etaInSeconds, line) -> {
                    if (progress >= 0 && progress <= 100) {
                        runOnUiThread(() -> {
                            progressBar.setIndeterminate(false);
                            progressBar.setProgress(Math.round(progress));
                            statusText.setText(String.format(
                                    Locale.ROOT,
                                    "Baixando %.1f%% | ETA %ds",
                                    progress,
                                    etaInSeconds
                            ));
                        });
                    } else if (line != null && !line.trim().isEmpty()) {
                        updateStatus(line, true);
                    }
                    return Unit.INSTANCE;
                });

                List<File> outputs = listOutputFiles(workDir);
                if (outputs.isEmpty()) {
                    throw new IllegalStateException("Download terminou, mas nenhum arquivo final foi encontrado.");
                }

                for (File output : outputs) {
                    updateStatus("Salvando " + output.getName(), true);
                    publishToDownloads(output, output.getName(), mimeFor(output));
                    savedCount++;
                }

                int finalSavedCount = savedCount;
                runOnUiThread(() -> {
                    setWorking(false, "Concluído. Arquivos salvos em Downloads/BaixarMusicaYouTube.");
                    toast(finalSavedCount == 1 ? "Download concluído." : finalSavedCount + " downloads concluídos.");
                });
            } catch (Exception ex) {
                String message = cleanError(ex);
                runOnUiThread(() -> {
                    setWorking(false, "Falha ao baixar.");
                    toast(message);
                });
            } finally {
                deleteTree(workDir);
            }
        });
    }

    private synchronized void ensureDownloaderReady() throws Exception {
        if (backendReady) {
            return;
        }
        updateStatus("Inicializando yt-dlp e FFmpeg...", true);
        YoutubeDL.getInstance().init(getApplicationContext());
        FFmpeg.getInstance().init(getApplicationContext());
        backendReady = true;
    }

    private void updateYtDlpIfPossible() {
        try {
            updateStatus("Atualizando yt-dlp...", true);
            YoutubeDL.getInstance().updateYoutubeDL(getApplicationContext(), YoutubeDL.UpdateChannel._STABLE);
        } catch (Exception ignored) {
            updateStatus("Usando yt-dlp empacotado...", true);
        }
    }

    private YoutubeDLRequest buildRequest(
            String url,
            String format,
            File workDir,
            boolean playlist,
            Double gifStart,
            Double gifEnd
    ) {
        YoutubeDLRequest request = new YoutubeDLRequest(url);
        request.addOption("--newline");
        request.addOption("--no-color");
        request.addOption("--no-mtime");
        request.addOption("--restrict-filenames");
        request.addOption("-o", new File(workDir, outputTemplate(playlist)).getAbsolutePath());
        if (!playlist) {
            request.addOption("--no-playlist");
        }

        switch (format) {
            case "mp3":
                request.addOption("-f", "bestaudio/best");
                request.addOption("--extract-audio");
                request.addOption("--audio-format", "mp3");
                request.addOption("--audio-quality", "192K");
                break;
            case "wav":
                request.addOption("-f", "bestaudio/best");
                request.addOption("--extract-audio");
                request.addOption("--audio-format", "wav");
                break;
            case "webm":
                request.addOption("-f", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best");
                request.addOption("--merge-output-format", "webm");
                break;
            case "mkv":
                request.addOption("-f", "bestvideo*+bestaudio/best");
                request.addOption("--merge-output-format", "mkv");
                request.addOption("--remux-video", "mkv");
                break;
            case "gif":
                double duration = gifEnd - gifStart;
                request.addOption("-f", "bestvideo[height<=720]/bestvideo/best");
                request.addOption("--recode-video", "gif");
                request.addOption("--postprocessor-args", "VideoConvertor+ffmpeg_i:-ss " + formatSeconds(gifStart));
                request.addOption("--postprocessor-args", "VideoConvertor+ffmpeg_o:-t "
                        + formatSeconds(duration)
                        + " -vf " + FILTRO_GIF
                        + " -an -loop 0");
                break;
            case "mp4":
            default:
                request.addOption("-f", "bestvideo*+bestaudio/best");
                request.addOption("--merge-output-format", "mp4");
                request.addOption("--remux-video", "mp4");
                break;
        }

        return request;
    }

    private String outputTemplate(boolean playlist) {
        if (playlist) {
            return "%(playlist_index)03d-%(title).90B.%(ext)s";
        }
        return "%(title).90B.%(ext)s";
    }

    private List<File> listOutputFiles(File workDir) {
        List<File> files = new ArrayList<>();
        collectFiles(workDir, files);
        files.removeIf(file -> {
            String name = file.getName().toLowerCase(Locale.ROOT);
            return name.endsWith(".part")
                    || name.endsWith(".ytdl")
                    || name.endsWith(".temp")
                    || name.endsWith(".tmp")
                    || file.length() <= 0;
        });
        files.sort((left, right) -> left.getName().compareToIgnoreCase(right.getName()));
        return files;
    }

    private void collectFiles(File file, List<File> files) {
        if (file == null || !file.exists()) {
            return;
        }
        if (file.isFile()) {
            files.add(file);
            return;
        }
        File[] children = file.listFiles();
        if (children == null) {
            return;
        }
        for (File child : children) {
            collectFiles(child, files);
        }
    }

    private Uri publishToDownloads(File source, String displayName, String mime) throws Exception {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, displayName);
        values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/BaixarMusicaYouTube");
        values.put(MediaStore.MediaColumns.IS_PENDING, 1);

        Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) {
            throw new IllegalStateException("Não foi possível criar arquivo em Downloads.");
        }

        try (FileInputStream input = new FileInputStream(source);
             OutputStream output = resolver.openOutputStream(uri)) {
            if (output == null) {
                throw new IllegalStateException("Não foi possível abrir o destino em Downloads.");
            }
            byte[] buffer = new byte[1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
        }

        values.clear();
        values.put(MediaStore.MediaColumns.IS_PENDING, 0);
        resolver.update(uri, values, null, null);
        return uri;
    }

    private String normalizeUrl(String url) {
        String value = url == null ? "" : url.trim();
        if (!value.isEmpty() && !value.contains("://")) {
            value = "https://" + value;
        }
        return value;
    }

    private boolean isYoutubeUrl(String url) {
        try {
            URI uri = URI.create(url);
            String host = uri.getHost();
            if (host == null) {
                return false;
            }
            host = host.toLowerCase(Locale.ROOT);
            return host.equals("youtube.com")
                    || host.equals("youtu.be")
                    || host.endsWith(".youtube.com");
        } catch (Exception ex) {
            return false;
        }
    }

    private double parseSeconds(String value, String fieldName) {
        String text = value == null ? "" : value.trim().replace(',', '.');
        if (text.isEmpty()) {
            throw new IllegalArgumentException("Informe o tempo " + fieldName + " do GIF.");
        }

        String[] parts = text.split(":");
        if (parts.length < 1 || parts.length > 3) {
            throw new IllegalArgumentException("Tempo " + fieldName + " inválido. Use segundos, mm:ss ou hh:mm:ss.");
        }

        try {
            double total;
            if (parts.length == 1) {
                total = Double.parseDouble(parts[0]);
            } else {
                double seconds = Double.parseDouble(parts[parts.length - 1]);
                int minutes = Integer.parseInt(parts[parts.length - 2]);
                int hours = parts.length == 3 ? Integer.parseInt(parts[0]) : 0;
                if (seconds >= 60 || minutes >= 60) {
                    throw new NumberFormatException();
                }
                total = hours * 3600 + minutes * 60 + seconds;
            }
            if (!Double.isFinite(total) || total < 0) {
                throw new NumberFormatException();
            }
            return total;
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException("Tempo " + fieldName + " inválido. Use segundos, mm:ss ou hh:mm:ss.");
        }
    }

    private void validateGifRange(double start, double end) {
        if (end <= start) {
            throw new IllegalArgumentException("O tempo final do GIF deve ser maior que o tempo inicial.");
        }
        if (end - start > DURACAO_MAXIMA_GIF) {
            throw new IllegalArgumentException("O trecho do GIF pode ter no máximo " + DURACAO_MAXIMA_GIF + " segundos.");
        }
    }

    private String formatSeconds(double seconds) {
        return String.format(Locale.ROOT, "%.3f", seconds);
    }

    private String mimeFor(File file) {
        String name = file.getName().toLowerCase(Locale.ROOT);
        if (name.endsWith(".mp4")) return "video/mp4";
        if (name.endsWith(".mp3")) return "audio/mpeg";
        if (name.endsWith(".webm")) return "video/webm";
        if (name.endsWith(".mkv")) return "video/x-matroska";
        if (name.endsWith(".gif")) return "image/gif";
        if (name.endsWith(".wav")) return "audio/wav";
        return "application/octet-stream";
    }

    private void setWorking(boolean working, String message) {
        buttonDownload.setEnabled(!working);
        spinnerFormato.setEnabled(!working);
        checkPlaylist.setEnabled(!working);
        inputUrl.setEnabled(!working);
        inputGifInicio.setEnabled(!working);
        inputGifFim.setEnabled(!working);
        progressBar.setIndeterminate(working);
        if (!working) {
            progressBar.setIndeterminate(false);
            progressBar.setProgress(working ? 0 : 100);
        }
        statusText.setText(message);
    }

    private void updateStatus(String message, boolean indeterminate) {
        runOnUiThread(() -> {
            statusText.setText(message);
            progressBar.setIndeterminate(indeterminate);
        });
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private String cleanError(Exception ex) {
        String message = ex.getMessage();
        if (message == null || message.trim().isEmpty()) {
            message = ex.toString();
        }
        message = message.replaceAll("\\x1B\\[[;\\d]*m", "").trim();
        return message.length() > 500 ? message.substring(0, 500) + "..." : message;
    }

    private void deleteTree(File file) {
        if (file == null || !file.exists()) {
            return;
        }
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) {
                for (File child : children) {
                    deleteTree(child);
                }
            }
        }
        //noinspection ResultOfMethodCallIgnored
        file.delete();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private LinearLayout.LayoutParams fullWidth() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
    }

    private LinearLayout.LayoutParams fullWidthHeight(int height) {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                height
        );
    }

    private LinearLayout.LayoutParams withBottomMargin(LinearLayout.LayoutParams params, int margin) {
        params.setMargins(0, 0, 0, margin);
        return params;
    }

    private GradientDrawable rounded(int color, int radius, int strokeColor, int strokeDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        if (strokeDp > 0) {
            drawable.setStroke(dp(strokeDp), strokeColor);
        }
        return drawable;
    }

    private android.graphics.drawable.Drawable roundedProgressDrawable() {
        GradientDrawable background = rounded(Color.rgb(55, 60, 70), dp(5), 0, 0);
        GradientDrawable progress = rounded(COR_VERMELHO, dp(5), 0, 0);
        android.graphics.drawable.ClipDrawable clipped = new android.graphics.drawable.ClipDrawable(
                progress,
                Gravity.START,
                android.graphics.drawable.ClipDrawable.HORIZONTAL
        );
        android.graphics.drawable.LayerDrawable layers = new android.graphics.drawable.LayerDrawable(
                new android.graphics.drawable.Drawable[]{background, clipped}
        );
        layers.setId(0, android.R.id.background);
        layers.setId(1, android.R.id.progress);
        return layers;
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
