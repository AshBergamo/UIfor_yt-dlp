package com.aipytorch.baixarmusicayoutube;

/** Small, linear-time blur on a private ARGB copy; no Android/GPU dependencies. */
final class ThumbnailBlur {
    private ThumbnailBlur() { }

    static int[] blur(int[] source, int width, int height, int radius) {
        if (width < 1 || height < 1 || radius < 0 || radius > 640
                || source == null || (long) width * height != source.length) {
            throw new IllegalArgumentException("Invalid image dimensions or blur radius");
        }
        int[] result = source.clone();
        int[] temporary = new int[result.length];
        for (int pass = 0; pass < 2; pass++) {
            blurAxis(result, temporary, width, height, radius, true);
            blurAxis(temporary, result, width, height, radius, false);
        }
        return result;
    }

    private static void blurAxis(int[] input, int[] output, int width, int height,
                                 int radius, boolean horizontal) {
        int length = horizontal ? width : height;
        int lines = horizontal ? height : width;
        int divisor = radius * 2 + 1;
        for (int line = 0; line < lines; line++) {
            int base = horizontal ? line * width : line;
            int step = horizontal ? 1 : width;
            int alpha = 0, red = 0, green = 0, blue = 0;
            for (int offset = -radius; offset <= radius; offset++) {
                int color = input[base + Math.max(0, Math.min(length - 1, offset)) * step];
                alpha += color >>> 24;
                red += (color >>> 16) & 255;
                green += (color >>> 8) & 255;
                blue += color & 255;
            }
            for (int position = 0; position < length; position++) {
                output[base + position * step] = ((alpha / divisor) << 24)
                        | ((red / divisor) << 16) | ((green / divisor) << 8) | (blue / divisor);
                int removed = input[base + Math.max(0, position - radius) * step];
                int added = input[base + Math.min(length - 1, position + radius + 1) * step];
                alpha += (added >>> 24) - (removed >>> 24);
                red += ((added >>> 16) & 255) - ((removed >>> 16) & 255);
                green += ((added >>> 8) & 255) - ((removed >>> 8) & 255);
                blue += (added & 255) - (removed & 255);
            }
        }
    }
}
