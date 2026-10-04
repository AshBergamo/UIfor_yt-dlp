package com.aipytorch.baixarmusicayoutube;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class SourcePolicyCheck {
    private static void checkNormalization() {
        String[][] cases = {
            {null, ""},
            {"", ""},
            {" \t ", ""},
            {" youtu.be/jNQXAC9IVRw ", "https://youtu.be/jNQXAC9IVRw"},
            {"www.youtube.com/watch?v=jNQXAC9IVRw", "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
            {" https://www.youtube.com/watch?v=jNQXAC9IVRw ", "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
            {"http://youtu.be/jNQXAC9IVRw", "http://youtu.be/jNQXAC9IVRw"},
            {"HTTPS://YOUTU.BE/jNQXAC9IVRw", "HTTPS://YOUTU.BE/jNQXAC9IVRw"}
        };
        for (String[] item : cases) {
            if (!SourcePolicy.normalize(item[0]).equals(item[1]))
                throw new AssertionError("URL normalization changed for " + item[0]);
        }
    }

    private static int checkFinalOutputs() {
        String[] formats = {"mp4", "mp3", "webm", "mkv", "gif", "wav"};
        int checked = 0;
        for (String format : formats) {
            for (String extension : formats) {
                String name = "movie." + extension;
                if (SourcePolicy.finalOutput(name, format) != format.equals(extension))
                    throw new AssertionError("Wrong-format file would be published: " + name + " as " + format);
                checked++;
            }
            for (String name : new String[]{"MOVIE." + format.toUpperCase(java.util.Locale.ROOT),
                    "movie.temple." + format, "movie.partners." + format}) {
                if (!SourcePolicy.finalOutput(name, format))
                    throw new AssertionError("Final file was rejected: " + name);
                checked++;
            }
            for (String name : new String[]{"movie.temp." + format, "movie.part." + format,
                    "movie." + format + ".part", "movie." + format + ".ytdl",
                    "movie." + format + ".temp", "movie." + format + ".tmp"}) {
                if (SourcePolicy.finalOutput(name, format))
                    throw new AssertionError("Intermediate file would be published: " + name);
                checked++;
            }
        }
        return checked;
    }

    public static void main(String[] args) throws Exception {
        List<String> lines = Files.readAllLines(Path.of(args[0]));
        List<SourcePolicy.Source> sources = new ArrayList<>();
        for (String line : lines) {
            String[] cells = line.split("\t", -1);
            if (!cells[0].equals("R")) continue;
            SourcePolicy.Rule rule = new SourcePolicy.Rule(cells[2].split(","), Boolean.parseBoolean(cells[3]), cells[4], Boolean.parseBoolean(cells[5]));
            sources.add(new SourcePolicy.Source(cells[1], cells[1], false, List.of(rule), List.of()));
        }
        SourcePolicy policy = new SourcePolicy(sources);
        int checked = 0;
        for (String line : lines) {
            String[] cells = line.split("\t", -1);
            if (!cells[0].equals("C")) continue;
            SourcePolicy.Match result = policy.classify(cells[1]);
            String actual = result == null ? "null" : result.source.id;
            if (!actual.equals(cells[2]) || result != null && result.shortLink != Boolean.parseBoolean(cells[3]))
                throw new AssertionError(cells[1] + " expected " + cells[2] + ", got " + actual);
            checked++;
        }
        if (!SourcePolicy.friendlyError("HTTP 429 https://cdn.test/?token=secret", "Instagram").contains("limitou"))
            throw new AssertionError("Readable error missing");
        if (SourcePolicy.friendlyError("HTTP 429 https://cdn.test/?token=secret", "Instagram").contains("token=secret"))
            throw new AssertionError("Signed URL leaked");
        checkNormalization();
        int outputsChecked = checkFinalOutputs();
        System.out.println("ANDROID_SOURCE_POLICY_OK: " + checked + " shared URL cases, 8 normalization cases, "
                + outputsChecked + " final/intermediate output cases");
    }
}
