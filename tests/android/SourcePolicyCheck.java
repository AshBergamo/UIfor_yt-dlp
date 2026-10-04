package com.aipytorch.baixarmusicayoutube;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class SourcePolicyCheck {
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
        if (!SourcePolicy.finalOutput("movie.mp4", "mp4") || SourcePolicy.finalOutput("movie.mp4", "mp3")
                || SourcePolicy.finalOutput("movie.temp.mp4", "mp4") || SourcePolicy.finalOutput("movie.part.webm", "webm"))
            throw new AssertionError("Intermediate/wrong-format file would be published");
        System.out.println("ANDROID_SOURCE_POLICY_OK: " + checked + " shared URL cases");
    }
}
