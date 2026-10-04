package com.aipytorch.baixarmusicayoutube;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipboardManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.text.InputType;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.yausername.youtubedl_android.YoutubeDL;
import com.yausername.youtubedl_android.YoutubeDLRequest;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import kotlin.Unit;

public class MainActivity extends Activity {
    private static final int DURACAO_MAXIMA_GIF = 30;
    private static final String META_PREFIX = "UIFOR_META:";
    private static final String FILTRO_GIF =
            "fps=15,scale=w='min(720,iw)':h=-2:flags=lanczos,"
                    + "split[quadros][paleta];"
                    + "[paleta]palettegen=max_colors=256:stats_mode=diff[cores];"
                    + "[quadros][cores]paletteuse=dither=sierra2_4a:diff_mode=rectangle";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final ExecutorService thumbnailExecutor = Executors.newSingleThreadExecutor();
    private final ExecutorService previewExecutor = Executors.newSingleThreadExecutor();
    private final Handler previewHandler = new Handler(Looper.getMainLooper());
    private final Runnable previewLookup = this::startPreviewLookup;
    private Future<?> previewTask;
    private volatile int previewGeneration;
    private volatile HttpURLConnection previewConnection;
    private String previewTarget = "", thumbnailAddress = "";
    private boolean previewAvailable;
    private SourcePolicy sourcePolicy;
    private MediaMetadata.Post postInfo;
    private MediaMetadata.Job previewMetadataJob, explicitMetadataJob;
    private Integer selectedPostIndex;
    private Button postButton;
    private LinearLayout postBox;
    private TextView sourceHelp, qualityText;
    private final String[] values = {"mp4", "mp3", "webm", "mkv", "gif", "wav"};
    private final String[] descriptions = {"MP4 · Vídeo", "MP3 · Áudio", "WEBM · Vídeo", "MKV · Vídeo", "GIF · Animação", "WAV · Áudio"};
    private int selectedIndex;
    private int bg, glow, panel, field, border, text, muted, accent, selected, error;
    private SharedPreferences preferences;
    private boolean light, working;
    private volatile boolean destroyed;
    private volatile int thumbnailGeneration;
    private volatile HttpURLConnection thumbnailConnection;
    private ScrollView scrollView;
    private MediaBackgroundDrawable mediaBackground;
    private LinearLayout root, gifBox;
    private EditText inputUrl, inputGifInicio, inputGifFim;
    private CheckBox checkPlaylist;
    private Button buttonDownload, buttonPaste, buttonOpen, themeLight, themeDark;
    private final List<Button> formatButtons = new ArrayList<>();
    private final List<TextView> artworkCaptions = new ArrayList<>();
    private ProgressBar progressBar;
    private TextView statusText, percentage, mediaTitle, formatText, resultTitle, details, errorText;
    private ImageView thumbnail;
    private Uri lastSavedUri;
    private String lastSavedMime;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try { sourcePolicy = MediaMetadata.loadPolicy(this); }
        catch (Exception error) { toast("Não foi possível carregar as fontes do aplicativo."); finish(); return; }
        preferences = getSharedPreferences("appearance", MODE_PRIVATE);
        light = preferences.getBoolean("light", false);
        buildUi();
        applyTheme();
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }
    }

    private TextView text(String value, int size, String role) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTag(role);
        view.setIncludeFontPadding(false);
        if (role.equals("title") || role.equals("label")) {
            view.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        }
        return view;
    }

    private Button button(String title, String role) {
        Button button = new Button(this);
        button.setText(title);
        button.setTextSize(14);
        button.setAllCaps(false);
        button.setTag(role);
        button.setMinHeight(dp(48));
        button.setMinimumHeight(dp(48));
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setPadding(dp(10), 0, dp(10), 0);
        return button;
    }

    private EditText input(String hint) {
        EditText view = new EditText(this);
        view.setHint(hint);
        view.setContentDescription(hint);
        view.setTextSize(14);
        view.setSingleLine(true);
        view.setInputType(InputType.TYPE_CLASS_TEXT);
        view.setPadding(dp(12), 0, dp(12), 0);
        view.setTag("input");
        return view;
    }

    private LinearLayout column() {
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        return view;
    }

    private LinearLayout row() {
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.HORIZONTAL);
        view.setGravity(Gravity.CENTER_VERTICAL);
        return view;
    }

    private void add(LinearLayout parent, View child, int bottom) {
        parent.addView(child, withBottomMargin(fullWidth(), dp(bottom)));
    }

    private LinearLayout card() {
        LinearLayout card = column();
        card.setTag("panel");
        card.setPadding(dp(18), dp(20), dp(18), dp(20));
        add(root, card, 18);
        return card;
    }

    private void buildUi() {
        scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        mediaBackground = new MediaBackgroundDrawable();
        scrollView.setBackground(mediaBackground);
        root = column();
        scrollView.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout header = row();
        ImageView logo = new ImageView(this);
        logo.setImageResource(com.aipytorch.baixarmusicayoutube.R.drawable.ic_launcher_foreground);
        logo.setTag("logo");
        header.addView(logo, new LinearLayout.LayoutParams(dp(48), dp(48)));
        LinearLayout brand = column();
        brand.setPadding(dp(12), 0, 0, 0);
        add(brand, text("UIfor_yt-dlp", 24, "title"), 4);
        add(brand, artworkCaption("Vídeos, áudio e GIFs", 13), 0);
        header.addView(brand, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        add(root, header, 18);
        LinearLayout utilities = row();
        themeLight = button("Claro", "themeLight");
        themeDark = button("Escuro", "themeDark");
        Button about = button("Sobre", "button");
        for (Button button : new Button[]{themeLight, themeDark, about}) {
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(48), 1);
            params.setMargins(0, 0, dp(8), 0);
            utilities.addView(button, params);
        }
        themeLight.setOnClickListener(view -> changeTheme(true));
        themeDark.setOnClickListener(view -> changeTheme(false));
        about.setOnClickListener(view -> showAbout());
        add(root, utilities, 24);
        add(root, text("Novo download", 28, "title"), 6);
        add(root, artworkCaption("Cole um link e escolha como salvar.", 14), 20);
        LinearLayout form = card();
        add(form, text("Link da mídia", 14, "label"), 10);
        LinearLayout urlRow = row();
        inputUrl = input("Cole o link aqui");
        inputUrl.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        urlRow.addView(inputUrl, new LinearLayout.LayoutParams(0, dp(50), 1));
        buttonPaste = button("Colar", "button");
        LinearLayout.LayoutParams pasteParams = new LinearLayout.LayoutParams(dp(72), dp(50));
        pasteParams.setMargins(dp(8), 0, 0, 0);
        urlRow.addView(buttonPaste, pasteParams);
        buttonPaste.setOnClickListener(view -> pasteLink());
        add(form, urlRow, 10);
        sourceHelp = text(sourcePolicy.help(), 12, "muted");
        add(form, sourceHelp, 14);
        postBox = column();
        add(postBox, text("Vídeos deste post", 14, "label"), 8);
        postButton = button("Todos os vídeos", "button");
        postButton.setContentDescription("Escolher vídeos deste post");
        postButton.setOnClickListener(view -> choosePostVideo());
        add(postBox, postButton, 0);
        postBox.setVisibility(View.GONE);
        add(form, postBox, 12);
        add(form, text("Formato de saída", 14, "label"), 10);
        for (int rowIndex = 0; rowIndex < 2; rowIndex++) {
            LinearLayout formats = row();
            for (int col = 0; col < 3; col++) {
                final int index = rowIndex * 3 + col;
                Button option = button(values[index].toUpperCase(Locale.ROOT), "format" + index);
                option.setContentDescription(descriptions[index]);
                option.setOnClickListener(view -> { selectedIndex = index; updateFormatUi(); applyTheme(); });
                formatButtons.add(option);
                LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(48), 1);
                params.setMargins(0, 0, col < 2 ? dp(8) : 0, 0);
                formats.addView(option, params);
            }
            add(form, formats, 8);
        }
        qualityText = text("Melhor qualidade disponível", 13, "muted");
        add(form, qualityText, 18);
        gifBox = column();
        add(gifBox, text("Intervalo do GIF", 14, "label"), 10);
        LinearLayout times = row();
        LinearLayout start = column(), end = column();
        add(start, text("Início", 13, "muted"), 6);
        add(end, text("Fim", 13, "muted"), 6);
        inputGifInicio = input("00:01");
        inputGifFim = input("00:03");
        start.addView(inputGifInicio, fullWidthHeight(dp(50)));
        end.addView(inputGifFim, fullWidthHeight(dp(50)));
        LinearLayout.LayoutParams half = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        half.setMargins(0, 0, dp(8), 0);
        times.addView(start, half);
        times.addView(end, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        add(gifBox, times, 8);
        add(gifBox, text("Trecho de até 30 segundos", 13, "muted"), 18);
        add(form, gifBox, 0);
        add(form, text("Pasta de destino", 14, "label"), 8);
        TextView destination = text("Downloads / BaixarMusicaYouTube", 13, "destination");
        destination.setPadding(dp(12), dp(14), dp(12), dp(14));
        add(form, destination, 16);
        checkPlaylist = new CheckBox(this);
        checkPlaylist.setText("Baixar playlist");
        checkPlaylist.setTag("muted");
        checkPlaylist.setTextSize(14);
        checkPlaylist.setMinHeight(dp(48));
        add(form, checkPlaylist, 12);
        buttonDownload = button("Baixar vídeo", "primary");
        form.addView(buttonDownload, fullWidthHeight(dp(52)));
        buttonDownload.setOnClickListener(view -> startDownload());
        LinearLayout status = card();
        resultTitle = text("Aguardando um download", 20, "title");
        add(status, resultTitle, 16);
        thumbnail = new ImageView(this);
        thumbnail.setTag("thumbnail");
        thumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
        thumbnail.setScaleType(ImageView.ScaleType.FIT_CENTER);
        thumbnail.setContentDescription("Miniatura da mídia");
        thumbnail.setClipToOutline(true);
        status.addView(thumbnail, withBottomMargin(new LinearLayout.LayoutParams(dp(176), dp(99)), dp(16)));
        mediaTitle = text("A mídia aparecerá aqui", 16, "label");
        add(status, mediaTitle, 8);
        formatText = text(descriptions[0], 13, "muted");
        add(status, formatText, 16);
        percentage = text("0%", 28, "title");
        add(status, percentage, 12);
        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        status.addView(progressBar, withBottomMargin(fullWidthHeight(dp(10)), dp(14)));
        statusText = text("Aguardando", 14, "muted");
        add(status, statusText, 8);
        details = text("A conversão começa após o download.", 13, "muted");
        add(status, details, 12);
        errorText = text("", 14, "error");
        errorText.setTextIsSelectable(true);
        errorText.setVisibility(View.GONE);
        add(status, errorText, 12);
        buttonOpen = button("Abrir arquivo", "button");
        buttonOpen.setEnabled(false);
        status.addView(buttonOpen, fullWidthHeight(dp(48)));
        buttonOpen.setOnClickListener(view -> openFile());
        TextView footer = artworkCaption("UIfor_yt-dlp · V3.3 · GPLv3\nDesenvolvido principalmente com IA", 12);
        footer.setGravity(Gravity.CENTER);
        add(root, footer, 0);
        updateFormatUi();
        setContentView(scrollView);
        // targetSdk 35 uses edge-to-edge on Android 15. Keep controls outside system bars.
        scrollView.setOnApplyWindowInsetsListener((view, insets) -> {
            int left, top, right, bottom;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                left = bars.left; top = bars.top; right = bars.right; bottom = bars.bottom;
                bottom = Math.max(bottom, insets.getInsets(WindowInsets.Type.ime()).bottom);
            } else {
                left = insets.getSystemWindowInsetLeft(); top = insets.getSystemWindowInsetTop();
                right = insets.getSystemWindowInsetRight(); bottom = insets.getSystemWindowInsetBottom();
            }
            view.setPadding(left, top, right, bottom);
            return Build.VERSION.SDK_INT >= 30 ? WindowInsets.CONSUMED : insets.consumeSystemWindowInsets();
        });
        scrollView.requestApplyInsets();
        updateContentPadding();
        inputUrl.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { schedulePreview(); }
            @Override public void afterTextChanged(Editable text) { }
        });
    }

    private void updateContentPadding() {
        int available = getResources().getDisplayMetrics().widthPixels;
        int padding = Math.max(dp(18), (available - dp(780)) / 2);
        root.setPadding(padding, dp(20), padding, dp(24));
    }

    @Override public void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration);
        updateContentPadding();
        scrollView.requestApplyInsets();
    }

    private void changeTheme(boolean useLight) {
        light = useLight;
        preferences.edit().putBoolean("light", light).apply();
        applyTheme();
    }

    private void applyTheme() {
        bg = Color.parseColor(light ? "#f4f6fa" : "#10151f");
        glow = Color.parseColor(light ? "#dfebf9" : "#22354c");
        panel = Color.parseColor(light ? "#fafcff" : "#1c2736");
        field = Color.parseColor(light ? "#ffffff" : "#152131");
        border = Color.parseColor(light ? "#b8cbe3" : "#40536c");
        text = Color.parseColor(light ? "#18212d" : "#f4f7fb");
        muted = Color.parseColor(light ? "#526277" : "#b4c3d5");
        accent = Color.parseColor(light ? "#0066cc" : "#4d9cff");
        selected = Color.parseColor(light ? "#e4f0ff" : "#203f64");
        error = Color.parseColor(light ? "#a52132" : "#ffaaaa");
        mediaBackground.setTheme(bg, glow, light);
        styleTree(root);
        progressBar.setProgressDrawable(roundedProgressDrawable());
        progressBar.setIndeterminateTintList(ColorStateList.valueOf(accent));
        checkPlaylist.setButtonTintList(new ColorStateList(new int[][]{new int[]{android.R.attr.state_checked}, new int[]{}}, new int[]{accent, muted}));
        themeLight.setSelected(light);
        themeDark.setSelected(!light);
        // Native system bar controls; theme changes in place without Activity recreation.
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                int flags = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                controller.setSystemBarsAppearance(light ? flags : 0, flags);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(light ? View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR : 0);
        }
    }

    private void styleTree(View view) {
        String role = view.getTag() instanceof String ? (String) view.getTag() : "";
        if (view instanceof TextView) {
            TextView label = (TextView) view;
            label.setTextColor(role.equals("muted") ? muted : role.equals("error") ? error : text);
            if (artworkCaptions.contains(label)) label.setTextColor(artworkCaptionColor());
        }
        if (view instanceof EditText) {
            EditText input = (EditText) view;
            input.setHintTextColor(muted);
            input.setBackground(rounded(field, dp(9), border, 1));
            input.setBackgroundTintList(null);
        } else if (view instanceof Button && !(view instanceof CheckBox)) {
            Button button = (Button) view;
            boolean active = role.equals("themeLight") && light || role.equals("themeDark") && !light
                    || role.startsWith("format") && role.equals("format" + selectedIndex);
            boolean primary = role.equals("primary");
            button.setBackgroundTintList(null);
            button.setBackground(rounded(primary ? (button.isEnabled() ? accent : selected) : active ? selected : field,
                    dp(9), active || primary ? accent : border, active ? 2 : 1));
            button.setTextColor(!button.isEnabled() ? muted : primary ? (light ? Color.WHITE : bg) : text);
            button.setAlpha(button.isEnabled() ? 1f : .65f);
            if (role.startsWith("format")) button.setSelected(active);
            if (Build.VERSION.SDK_INT >= 30) button.setStateDescription(active ? "Selecionado" : "");
        } else if (role.equals("panel")) {
            view.setBackground(rounded(backgroundPanelColor(), dp(18), border, 1));
        } else if (role.equals("destination") || role.equals("thumbnail")) {
            view.setBackground(rounded(field, dp(9), border, role.equals("destination") ? 1 : 0));
        } else if (role.equals("logo")) {
            view.setBackground(rounded(Color.rgb(32, 55, 81), dp(12), border, 1));
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) styleTree(group.getChildAt(i));
        }
    }

    private void pasteLink() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        if (clipboard.hasPrimaryClip() && clipboard.getPrimaryClip() != null && clipboard.getPrimaryClip().getItemCount() > 0) {
            CharSequence value = clipboard.getPrimaryClip().getItemAt(0).coerceToText(this);
            inputUrl.setText(value == null ? "" : value.toString().trim());
            inputUrl.requestFocus();
        }
    }

    private void showAbout() {
        String message = "UIfor_yt-dlp · V3.3\nVídeos, áudio e GIFs\nLicença GPLv3 · Vinícius\n\n"
                + "O projeto começou sem inteligência artificial e era fechado. A IA passou a produzir sua evolução inicialmente como um experimento de capacidade de modelos, principalmente da OpenAI, e depois se tornou a principal forma de desenvolvimento e manutenção. A interface e as integrações de download são produzidas de maneira amplamente autônoma, com orientação humana e pouca edição direta do código. A primeira versão disponibilizada publicamente é a v3.\n\n"
                + "As bibliotecas têm seus próprios autores e licenças. Os downloads são executados por yt-dlp e FFmpeg; não dependem de um modelo de IA.\n\nFontes integradas: " + sourcePolicy.help() + ". Links públicos individuais e playlists do YouTube. A disponibilidade depende do site e do link.";
        TextView dialogTitle = text("Sobre", 20, "title");
        dialogTitle.setPadding(dp(24), dp(22), dp(24), dp(8));
        dialogTitle.setTextColor(text);
        AlertDialog dialog = new AlertDialog.Builder(this).setCustomTitle(dialogTitle).setMessage(message).setPositiveButton("Fechar", null).create();
        dialog.setOnShowListener(ignored -> {
            dialog.getWindow().setBackgroundDrawable(rounded(panel, dp(16), border, 1));
            TextView content = dialog.findViewById(android.R.id.message);
            if (content != null) content.setTextColor(text);
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(accent);
        });
        dialog.show();
    }

    private void updateFormatUi() {
        String format = selectedFormat();
        gifBox.setVisibility("gif".equals(format) ? View.VISIBLE : View.GONE);
        formatText.setText(descriptions[selectedIndex]);
        qualityText.setText("webm".equals(selectedFormat()) ? "WEBM: conversão quando necessária; pode demorar mais" : "Melhor qualidade disponível");
        if (!working) buttonDownload.setText("gif".equals(format) ? "Gerar GIF" : "mp3".equals(format) || "wav".equals(format) ? "Extrair áudio" : "Baixar vídeo");
    }

    private String selectedFormat() { return values[selectedIndex]; }

    private void showError(String message) {
        errorText.setText(message);
        errorText.setVisibility(View.VISIBLE);
        scrollView.post(() -> {
            android.graphics.Rect bounds = new android.graphics.Rect();
            errorText.getDrawingRect(bounds);
            root.offsetDescendantRectToMyCoords(errorText, bounds);
            scrollView.smoothScrollTo(0, bounds.top);
        });
    }

    private void startDownload() {
        if (working) return;
        errorText.setVisibility(View.GONE);
        String url = SourcePolicy.normalize(inputUrl.getText().toString());
        SourcePolicy.Match source = sourcePolicy.classify(url);
        if (source == null) { showError("Informe um link de vídeo de uma das fontes aceitas. Perfis, stories e outras fontes ficam para uma próxima etapa."); inputUrl.requestFocus(); return; }
        String format = selectedFormat();
        Double gifStart = null, gifEnd = null;
        if ("gif".equals(format)) {
            try {
                gifStart = parseSeconds(inputGifInicio.getText().toString(), "inicial");
                gifEnd = parseSeconds(inputGifFim.getText().toString(), "final");
                validateGifRange(gifStart, gifEnd);
            } catch (IllegalArgumentException ex) { showError(ex.getMessage()); return; }
        }
        if (!source.source.id.equals("youtube") && postInfo == null) { lookupPostExplicit(url); return; }
        MediaMetadata.Post capturedPost = postInfo;
        Integer capturedSelection = selectedPostIndex;
        String downloadUrl = capturedPost != null ? capturedPost.url : url;
        boolean playlist = source.source.id.equals("youtube") && checkPlaylist.isChecked();
        Double finalGifStart = gifStart, finalGifEnd = gifEnd;
        File workDir = new File(getCacheDir(), "yt_download_work");
        lastSavedUri = null;
        cancelPreviewLookup();
        if (!previewAvailable) {
            clearMediaPreview();
            mediaTitle.setText("Lendo informações da mídia…");
        }
        details.setText(playlist ? "Playlist · acompanhando a mídia atual" : "A conversão começa após o download.");
        resultTitle.setText("Download em andamento");
        setWorking(true, "Preparando…");
        executor.execute(() -> {
            int savedCount = 0;
            try {
                ensureDownloaderReady();
                deleteTree(workDir);
                if (!workDir.mkdirs() && !workDir.isDirectory()) throw new IllegalStateException("Não foi possível preparar a pasta temporária.");
                YoutubeDLRequest request = buildRequest(downloadUrl, format, workDir, playlist, finalGifStart, finalGifEnd, capturedPost, capturedSelection);
                updateStatus("Lendo informações da mídia…");
                String processId = "download-" + System.currentTimeMillis();
                Exception transferError = null;
                try {
                YoutubeDL.getInstance().execute(request, processId, true, (progress, eta, line) -> {
                    if (line != null && line.startsWith(META_PREFIX)) {
                        readMetadata(line.substring(META_PREFIX.length()));
                    } else if (line != null && line.startsWith("[download]") && line.contains("%") && progress >= 0 && progress <= 100) {
                        ui(() -> {
                            progressBar.setIndeterminate(false);
                            progressBar.setProgress(Math.round(progress));
                            percentage.setText(String.format(Locale.ROOT, "%.0f%%", progress));
                            statusText.setText("Baixando a mídia atual");
                            details.setText(eta >= 0 ? "Tempo estimado: " + eta + " s" : "Tamanho ou tempo estimado indisponível");
                            buttonDownload.setText("Baixando…");
                        });
                    } else if (line != null && line.startsWith("[EmbedThumbnail]")) {
                        updateStatus("Incorporando a capa original ao vídeo…");
                    } else if (line != null && line.startsWith("[ThumbnailsConvertor]")) {
                        updateStatus("Preparando a capa original…");
                    } else if (line != null && (line.startsWith("[Merger]") || line.startsWith("[Video") || line.startsWith("[ExtractAudio]") || line.startsWith("size="))) {
                        updateStatus("Convertendo a mídia…");
                    } else if (line != null && line.startsWith("[download]")) {
                        updateStatus("Baixando a mídia atual…");
                    }
                    return Unit.INSTANCE;
                });
                } catch (Exception error) {
                    if (capturedPost == null) throw error;
                    transferError = error;
                }
                List<File> outputs = listOutputFiles(workDir, format);
                if (outputs.isEmpty()) {
                    if (transferError != null) throw transferError;
                    throw new IllegalStateException("Download terminou, mas nenhum arquivo final foi encontrado.");
                }
                Uri savedUri = null;
                String savedMime = null;
                for (File output : outputs) {
                    updateStatus("Salvando " + output.getName());
                    savedMime = mimeFor(output);
                    savedUri = publishToDownloads(output, output.getName(), savedMime);
                    savedCount++;
                    lastSavedUri = savedUri;
                    lastSavedMime = savedMime;
                }
                if (transferError != null) throw new IllegalStateException("Download parcial: " + savedCount
                        + " arquivo(s) salvo(s). Alguns vídeos do post falharam; os arquivos concluídos foram preservados.");
                int count = savedCount;
                Uri finalUri = savedUri;
                String finalMime = savedMime;
                ui(() -> {
                    lastSavedUri = finalUri; lastSavedMime = finalMime;
                    resultTitle.setText("Download concluído");
                    progressBar.setIndeterminate(false);
                    progressBar.setProgress(100);
                    percentage.setText("100%");
                    setWorking(false, count == 1 ? "Arquivo salvo em Downloads." : count + " arquivos salvos em Downloads.");
                    details.setText("Downloads / BaixarMusicaYouTube");
                    buttonOpen.setText(count == 1 ? "Abrir arquivo" : "Abrir último arquivo");
                });
            } catch (Exception ex) {
                String rawMessage = cleanError(ex);
                String message = rawMessage.startsWith("Download parcial:") ? rawMessage
                        : (savedCount > 0 ? savedCount + " arquivo(s) já salvo(s).\n" : "")
                          + SourcePolicy.friendlyError(rawMessage, source.source.name);
                ui(() -> {
                    resultTitle.setText("Não foi possível concluir");
                    progressBar.setIndeterminate(false);
                    progressBar.setProgress(0);
                    percentage.setText("0%");
                    setWorking(false, "Falha ao baixar.");
                    showError(message);
                });
            } finally { deleteTree(workDir); }
        });
    }

    private String previewVideoUrl(String input) {
        try {
            String normalized = SourcePolicy.normalize(input);
            Uri uri = Uri.parse(normalized);
            if (!("https".equals(uri.getScheme()) || "http".equals(uri.getScheme())) || !isYoutubeUrl(normalized)) return "";
            List<String> parts = uri.getPathSegments();
            String id = "";
            if ("youtu.be".equalsIgnoreCase(uri.getHost()) && parts.size() == 1) {
                id = parts.get(0);
            } else if (parts.size() == 2 && (parts.get(0).equals("shorts") || parts.get(0).equals("live")
                    || parts.get(0).equals("embed") || parts.get(0).equals("v") || parts.get(0).equals("e"))) {
                id = parts.get(1);
            } else if (parts.size() == 1 && parts.get(0).equals("watch")) {
                id = uri.getQueryParameter("v");
            }
            return id != null && id.matches("[A-Za-z0-9_-]{11}") ? "https://www.youtube.com/watch?v=" + id : "";
        } catch (Exception ignored) { return ""; }
    }

    private void cancelPreviewLookup() {
        previewGeneration++;
        if (previewMetadataJob != null) previewMetadataJob.cancel();
        previewMetadataJob = null;
        previewHandler.removeCallbacks(previewLookup);
        if (previewTask != null) previewTask.cancel(true);
        HttpURLConnection previous = previewConnection;
        if (previous != null) previous.disconnect();
    }

    private void clearMediaPreview() {
        thumbnailGeneration++;
        thumbnailAddress = "";
        HttpURLConnection previous = thumbnailConnection;
        if (previous != null) previous.disconnect();
        thumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
        setBackgroundImage(null);
        mediaTitle.setText("A mídia aparecerá aqui");
    }

    private void schedulePreview() {
        if (working || destroyed) return;
        SourcePolicy.Match source = sourcePolicy.classify(inputUrl.getText().toString());
        String target = source == null ? "" : source.source.id.equals("youtube")
                ? previewVideoUrl(source.url) : source.url;
        sourceHelp.setText(source == null ? sourcePolicy.help() : source.source.name
                + (source.source.experimental ? " · Experimental" : "") + " · Link público");
        checkPlaylist.setVisibility(source == null || source.source.id.equals("youtube") ? View.VISIBLE : View.GONE);
        if (target.equals(previewTarget)) return;
        cancelPreviewLookup();
        previewTarget = target;
        previewAvailable = false;
        postInfo = null;
        selectedPostIndex = null;
        postBox.setVisibility(View.GONE);
        clearMediaPreview();
        if (!target.isEmpty()) previewHandler.postDelayed(previewLookup, 450);
    }

    private void startPreviewLookup() {
        if (working || destroyed || previewTarget.isEmpty()) return;
        String target = previewTarget;
        int generation = previewGeneration;
        SourcePolicy.Match source = sourcePolicy.classify(target);
        if (source != null && !source.source.id.equals("youtube")) {
            MediaMetadata.Job job = new MediaMetadata.Job();
            previewMetadataJob = job;
            previewTask = previewExecutor.submit(() -> {
                try {
                    MediaMetadata.Post info = job.lookup(getApplicationContext(), sourcePolicy, target, null);
                    ui(() -> {
                        if (!working && generation == previewGeneration && target.equals(previewTarget)) acceptPostInfo(info);
                    });
                } catch (Exception ignored) { /* Optional preview stays silent. */ }
            });
            previewHandler.postDelayed(() -> {
                if (generation == previewGeneration && !previewAvailable) cancelPreviewLookup();
            }, 12000);
        } else previewTask = previewExecutor.submit(() -> fetchPreview(target, generation));
    }

    private void fetchPreview(String target, int generation) {
        HttpURLConnection connection = null;
        try {
            if (destroyed || generation != previewGeneration) return;
            URL url = new URL("https://www.youtube.com/oembed?format=json&url=" + URLEncoder.encode(target, "UTF-8"));
            connection = (HttpURLConnection) url.openConnection();
            previewConnection = connection;
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);
            connection.setRequestProperty("Accept", "application/json");
            if (connection.getResponseCode() != 200 || connection.getContentLengthLong() > 128 * 1024) return;
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            long deadline = System.nanoTime() + 6_000_000_000L;
            try (InputStream input = connection.getInputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (destroyed || generation != previewGeneration || Thread.currentThread().isInterrupted()
                            || bytes.size() + count > 128 * 1024 || System.nanoTime() > deadline) return;
                    bytes.write(buffer, 0, count);
                }
            }
            JSONObject info = new JSONObject(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
            Object title = info.opt("title");
            if (!(title instanceof String) || ((String) title).trim().isEmpty()) return;
            String image = info.optString("thumbnail_url", "");
            ui(() -> {
                if (!working && generation == previewGeneration && target.equals(previewTarget)) {
                    previewAvailable = true;
                    showMetadata((String) title, image);
                }
            });
        } catch (Exception ignored) { /* The preview is optional and has no error UI. */ }
        finally {
            if (connection != null) connection.disconnect();
            if (previewConnection == connection) previewConnection = null;
        }
    }

    private void readMetadata(String json) {
        try {
            JSONObject metadata = new JSONObject(json);
            String title = metadata.optString("title", "Mídia em andamento");
            String url = metadata.optString("thumbnail", "");
            ui(() -> showMetadata(title, url));
        } catch (Exception ignored) { /* Optional metadata does not affect the media operation. */ }
    }

    private void showMetadata(String title, String url) {
        mediaTitle.setText(title.length() > 300 ? title.substring(0, 300) : title);
        if (working) {
            progressBar.setIndeterminate(true);
            percentage.setText("…");
        }
        if (url.equals(thumbnailAddress)) return;
        int generation = ++thumbnailGeneration;
        thumbnailAddress = url;
        HttpURLConnection previous = thumbnailConnection;
        if (previous != null) previous.disconnect();
        thumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
        // Separate from both metadata lookup and the download worker.
        setBackgroundImage(null);
        if (!url.isEmpty()) thumbnailExecutor.execute(() -> loadThumbnail(url, generation));
    }

    private void loadThumbnail(String address, int generation) {
        HttpURLConnection connection = null;
        try {
            if (destroyed || generation != thumbnailGeneration) return;
            URL url = new URL(address);
            if (!url.getProtocol().equals("https")) return;
            connection = (HttpURLConnection) url.openConnection();
            thumbnailConnection = connection;
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);
            connection.setRequestProperty("Accept", "image/*");
            if (connection.getContentLengthLong() > 8 * 1024 * 1024) return;
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            long deadline = System.nanoTime() + 10_000_000_000L;
            try (InputStream input = connection.getInputStream()) {
                byte[] buffer = new byte[8192];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (destroyed || generation != thumbnailGeneration || bytes.size() + count > 8 * 1024 * 1024 || System.nanoTime() > deadline) return;
                    bytes.write(buffer, 0, count);
                }
            }
            byte[] data = bytes.toByteArray();
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeByteArray(data, 0, data.length, options);
            if (options.outWidth <= 0 || options.outHeight <= 0 || (long) options.outWidth * options.outHeight > 25_000_000) return;
            options.inJustDecodeBounds = false;
            options.inSampleSize = 1;
            while (Math.max(options.outWidth, options.outHeight) / options.inSampleSize > 1024) options.inSampleSize *= 2;
            Bitmap bitmap = BitmapFactory.decodeByteArray(data, 0, data.length, options);
            if (bitmap != null && !destroyed && generation == thumbnailGeneration) {
                Bitmap prepared = null;
                try {
                    prepared = MediaBackgroundDrawable.prepare(bitmap);
                } catch (RuntimeException | OutOfMemoryError ignored) { /* Keep the normal gradient. */ }
                Bitmap background = prepared;
                ui(() -> {
                    if (generation == thumbnailGeneration) {
                        thumbnail.setImageBitmap(bitmap);
                        setBackgroundImage(background);
                    }
                });
            }
        } catch (Exception ignored) { /* Keep the generic placeholder. */ }
        finally {
            if (connection != null) connection.disconnect();
            if (thumbnailConnection == connection) thumbnailConnection = null;
        }
    }

    private int backgroundPanelColor() {
        return mediaBackground.hasImage() ? (panel & 0x00ffffff) | (214 << 24) : panel;
    }

    private TextView artworkCaption(String content, int size) {
        TextView label = text(content, size, "muted");
        artworkCaptions.add(label);
        return label;
    }

    private int artworkCaptionColor() {
        return mediaBackground.hasImage() ? (light ? text : Color.WHITE) : muted;
    }

    private void updateBackgroundPanels(View view) {
        if ("panel".equals(view.getTag())) {
            view.setBackground(rounded(backgroundPanelColor(), dp(18), border, 1));
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++) updateBackgroundPanels(group.getChildAt(index));
        }
    }

    private void setBackgroundImage(Bitmap bitmap) {
        boolean previous = mediaBackground.hasImage();
        mediaBackground.setImage(bitmap);
        if (previous != mediaBackground.hasImage()) {
            updateBackgroundPanels(root);
            for (TextView caption : artworkCaptions) caption.setTextColor(artworkCaptionColor());
        }
    }

    private void openFile() {
        if (lastSavedUri == null) return;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(lastSavedUri, lastSavedMime).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
        } catch (android.content.ActivityNotFoundException ex) { toast("Abra a pasta Downloads em um gerenciador de arquivos."); }
    }

    private void ui(Runnable action) { runOnUiThread(() -> { if (!destroyed) action.run(); }); }

    private void setWorking(boolean value, String message) {
        working = value;
        for (View control : new View[]{buttonDownload, buttonPaste, checkPlaylist, postButton, inputUrl, inputGifInicio, inputGifFim}) control.setEnabled(!working);
        for (Button format : formatButtons) format.setEnabled(!working);
        buttonOpen.setEnabled(!working && lastSavedUri != null);
        if (working) {
            progressBar.setProgress(0);
            progressBar.setIndeterminate(true);
            percentage.setText("…");
            buttonDownload.setText("Processando…");
        } else { updateFormatUi(); }
        statusText.setText(message);
        applyTheme();
    }

    private void updateStatus(String message) {
        ui(() -> {
            statusText.setText(message);
            progressBar.setIndeterminate(true);
            percentage.setText("…");
            if (working) buttonDownload.setText("Processando…");
        });
    }

    private void toast(String message) { Toast.makeText(this, message, Toast.LENGTH_LONG).show(); }

    private void handleBack() {
        if (working) { toast("Aguarde o download terminar antes de sair."); return; }
        finish();
    }

    @Override public void onBackPressed() { handleBack(); }

    @Override protected void onDestroy() {
        destroyed = true;
        cancelPreviewLookup();
        previewExecutor.shutdownNow();
        if (explicitMetadataJob != null) explicitMetadataJob.cancel();
        thumbnailGeneration++;
        HttpURLConnection connection = thumbnailConnection;
        if (connection != null) connection.disconnect();
        thumbnailExecutor.shutdownNow();
        executor.shutdownNow();
        if (mediaBackground != null) mediaBackground.clear();
        super.onDestroy();
    }

    private void ensureDownloaderReady() throws Exception {
        MediaMetadata.prepare(getApplicationContext(), this::updateStatus);
    }

    private void lookupPostExplicit(String url) {
        cancelPreviewLookup();
        setWorking(true, "Lendo vídeos do post…");
        MediaMetadata.Job job = new MediaMetadata.Job();
        explicitMetadataJob = job;
        Runnable timeout = job::cancel;
        previewHandler.postDelayed(timeout, 45000);
        executor.execute(() -> {
            try {
                MediaMetadata.Post info = job.lookup(getApplicationContext(), sourcePolicy, url, this::updateStatus);
                ui(() -> {
                    setWorking(false, "Escolha um vídeo ou todos e clique em Baixar.");
                    acceptPostInfo(info);
                    if (info.videos.size() == 1) startDownload();
                });
            } catch (Exception error) {
                SourcePolicy.Match match = sourcePolicy.classify(url);
                String message = SourcePolicy.friendlyError(cleanError(error), match != null ? match.source.name : "essa fonte");
                ui(() -> { setWorking(false, "Não foi possível ler o post."); showError(message); });
            } finally { previewHandler.removeCallbacks(timeout); explicitMetadataJob = null; }
        });
    }

    private void acceptPostInfo(MediaMetadata.Post info) {
        postInfo = info;
        SourcePolicy.Match source = sourcePolicy.classify(info.url);
        if (source != null) sourceHelp.setText(source.source.name + (source.source.experimental ? " · Experimental" : "") + " · Link público");
        selectedPostIndex = null;
        previewAvailable = true;
        postBox.setVisibility(info.videos.size() > 1 ? View.VISIBLE : View.GONE);
        showPostSelection();
    }

    private void choosePostVideo() {
        if (postInfo == null || working) return;
        MediaMetadata.Post info = postInfo;
        String[] labels = new String[info.videos.size() + 1];
        labels[0] = "Todos os vídeos (" + info.videos.size() + ")";
        int selected = 0;
        for (int n = 0; n < info.videos.size(); n++) {
            JSONObject item = info.videos.get(n);
            labels[n + 1] = "Vídeo " + (n + 1) + " — " + item.optString("title", "Vídeo");
            if (selectedPostIndex != null && selectedPostIndex == item.optInt("index")) selected = n + 1;
        }
        new AlertDialog.Builder(this).setTitle("Vídeos deste post").setSingleChoiceItems(labels, selected, (dialog, index) -> {
            if (postInfo == info) {
                selectedPostIndex = index == 0 ? null : info.videos.get(index - 1).optInt("index");
                showPostSelection();
            }
            dialog.dismiss();
        }).setNegativeButton("Fechar", null).show();
    }

    private void showPostSelection() {
        if (postInfo == null) return;
        JSONObject selected = postInfo.videos.get(0);
        int ordinal = 1;
        for (int n = 0; n < postInfo.videos.size(); n++) {
            JSONObject item = postInfo.videos.get(n);
            if (selectedPostIndex != null && selectedPostIndex == item.optInt("index")) { selected = item; ordinal = n + 1; break; }
        }
        postButton.setText(selectedPostIndex == null ? "Todos os vídeos (" + postInfo.videos.size() + ")" : "Vídeo " + ordinal);
        showMetadata(selected.optString("title", "Vídeo"), selected.isNull("thumbnail") ? "" : selected.optString("thumbnail", ""));
    }

    private YoutubeDLRequest buildRequest(
            String url,
            String format,
            File workDir,
            boolean playlist,
            Double gifStart,
            Double gifEnd,
            MediaMetadata.Post post,
            Integer selection
    ) {
        YoutubeDLRequest request = new YoutubeDLRequest(url);
        request.addOption("--newline");
        request.addOption("--no-simulate");
        request.addOption("--progress");
        request.addOption("--print", "before_dl:" + META_PREFIX + "{\"title\":%(title)j,\"thumbnail\":%(thumbnail)j}");
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
                request.addOption("-f", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/bestvideo*+bestaudio/best");
                request.addOption("--merge-output-format", "webm/mp4/mkv");
                request.addOption("--recode-video", "webm");
                request.addOption("--postprocessor-args", "VideoConvertor+ffmpeg_o:-c:v libvpx-vp9 -crf 32 -b:v 0 -cpu-used 4 -c:a libopus");
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

        if (post != null) {
            List<String> indices = new ArrayList<>();
            for (JSONObject item : post.videos) {
                int index = item.optInt("index");
                if (selection == null || selection == index) indices.add(Integer.toString(index));
            }
            if (indices.isEmpty()) throw new IllegalArgumentException("Esse vídeo não está mais disponível. Cole o link novamente.");
            request.addOption("--playlist-items", String.join(",", indices));
            request.addOption("--use-extractors", sourcePolicy.extractors());
            request.addOption("--match-filter", "!is_live");
            if (selection == null && indices.size() > 1) request.addOption("--ignore-errors");
            request.addOption("-o", new File(workDir, "%(id)s-%(playlist_index|1)s-%(title).90B.%(ext)s").getAbsolutePath());
        }
        if (format.equals("mp4") || format.equals("mkv")) {
            request.addOption("--embed-thumbnail");
            request.addOption("--convert-thumbnails", "jpg");
        }
        return request;
    }

    private String outputTemplate(boolean playlist) {
        if (playlist) {
            return "%(playlist_index)03d-%(title).90B.%(ext)s";
        }
        return "%(title).90B.%(ext)s";
    }

    private List<File> listOutputFiles(File workDir, String format) {
        List<File> files = new ArrayList<>();
        collectFiles(workDir, files);
        files.removeIf(file -> !SourcePolicy.finalOutput(file.getName(), format) || file.length() <= 0);
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
        GradientDrawable background = rounded(border, dp(5), 0, 0);
        GradientDrawable progress = rounded(accent, dp(5), 0, 0);
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

}
