package com.aipytorch.baixarmusicayoutube;

import java.util.Arrays;
import java.util.Random;

/** Host-side checks of the CPU filter, independently of Android rendering. */
public final class ThumbnailBlurCheck {
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static int[] reference(int[] input, int width, int height, int radius) {
        int[] result = input.clone();
        for (int direction : new int[]{0, 1, 0, 1}) {
            int[] output = new int[result.length];
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    int color = 0;
                    for (int shift : new int[]{0, 8, 16, 24}) {
                        int total = 0;
                        for (int offset = -radius; offset <= radius; offset++) {
                            int sampleX = Math.max(0, Math.min(width - 1, x + (direction == 0 ? offset : 0)));
                            int sampleY = Math.max(0, Math.min(height - 1, y + (direction == 1 ? offset : 0)));
                            total += (result[sampleY * width + sampleX] >>> shift) & 255;
                        }
                        color |= (total / (2 * radius + 1)) << shift;
                    }
                    output[y * width + x] = color;
                }
            }
            result = output;
        }
        return result;
    }

    public static void main(String[] args) {
        Random random = new Random(20261004);
        for (int[] size : new int[][]{{1, 1}, {1, 15}, {17, 1}, {2, 3}, {23, 17}}) {
            for (int radius : new int[]{0, 1, 3, 8}) {
                int width = size[0], height = size[1];
                int[] image = new int[width * height];
                for (int i = 0; i < image.length; i++) image[i] = random.nextInt();
                int[] original = image.clone();
                int[] actual = ThumbnailBlur.blur(image, width, height, radius);
                require(Arrays.equals(actual, reference(image, width, height, radius)), "Filter or edge mismatch");
                require(Arrays.equals(image, original) && image != actual, "Original was modified/shared");
            }
        }
        for (int color : new int[]{0xff000000, 0xffffffff, 0xffe84d23, 0x80ff00ff, 0}) {
            int[] image = new int[57];
            Arrays.fill(image, color);
            require(Arrays.equals(image, ThumbnailBlur.blur(image, 19, 3, 3)), "Solid color/alpha changed");
        }
        for (int[] invalid : new int[][]{{0, 1, 3}, {1, -1, 3}, {1, 1, -1}, {1, 1, 641}, {2, 2, 3}, {Integer.MAX_VALUE, 2, 3}}) {
            boolean rejected = false;
            try { ThumbnailBlur.blur(new int[1], invalid[0], invalid[1], invalid[2]); }
            catch (IllegalArgumentException expected) { rejected = true; }
            require(rejected, "Invalid dimensions accepted");
        }
        int[] large = new int[640 * 640];
        Arrays.fill(large, 0xffabcdef);
        long start = System.nanoTime();
        require(Arrays.equals(large, ThumbnailBlur.blur(large, 640, 640, 3)), "Maximum cache changed");
        System.out.printf("Android CPU blur checks passed (640 x 640: %.1f ms).%n", (System.nanoTime() - start) / 1e6);
    }
}
