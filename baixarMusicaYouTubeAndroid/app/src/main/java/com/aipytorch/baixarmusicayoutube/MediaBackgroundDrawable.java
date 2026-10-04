package com.aipytorch.baixarmusicayoutube;

import android.animation.ValueAnimator;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;
import android.view.animation.DecelerateInterpolator;

/** A stationary backdrop; the scrolling controls are painted separately. */
final class MediaBackgroundDrawable extends Drawable {
    private final Paint gradientPaint = new Paint();
    private final Paint imagePaint = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
    private final Paint overlayPaint = new Paint();
    private final RectF destination = new RectF();
    private Bitmap image;
    private ValueAnimator animation;
    private int base = 0xff10151f, glow = 0xff22354c, alpha = 255;
    private boolean light;
    private float intensity;

    static Bitmap prepare(Bitmap original) {
        int width = original.getWidth(), height = original.getHeight();
        float scale = Math.min(1f, 640f / Math.max(width, height));
        int reducedWidth = Math.max(1, Math.round(width * scale));
        int reducedHeight = Math.max(1, Math.round(height * scale));
        Bitmap reduced = Bitmap.createScaledBitmap(original, reducedWidth, reducedHeight, true);
        int[] pixels = new int[reducedWidth * reducedHeight];
        reduced.getPixels(pixels, 0, reducedWidth, 0, 0, reducedWidth, reducedHeight);
        int[] blurred = ThumbnailBlur.blur(pixels, reducedWidth, reducedHeight, 3);
        return Bitmap.createBitmap(blurred, reducedWidth, reducedHeight, Bitmap.Config.ARGB_8888);
    }

    boolean hasImage() { return image != null; }

    void setTheme(int newBase, int newGlow, boolean useLight) {
        base = newBase;
        glow = newGlow;
        light = useLight;
        rebuildGradient();
        invalidateSelf();
    }

    void setImage(Bitmap prepared) {
        clear();
        if (prepared == null) return;
        image = prepared;
        updateDestination();
        if (!ValueAnimator.areAnimatorsEnabled()) {
            intensity = 1f;
            invalidateSelf();
            return;
        }
        animation = ValueAnimator.ofFloat(0f, 1f);
        animation.setDuration(250);
        animation.setInterpolator(new DecelerateInterpolator(1.5f));
        animation.addUpdateListener(value -> {
            intensity = (float) value.getAnimatedValue();
            invalidateSelf();
        });
        animation.start();
    }

    void clear() {
        if (animation != null) {
            animation.cancel();
            animation.removeAllUpdateListeners();
            animation = null;
        }
        image = null;
        intensity = 0f;
        invalidateSelf();
    }

    @Override protected void onBoundsChange(Rect bounds) {
        rebuildGradient();
        updateDestination();
    }

    private void rebuildGradient() {
        Rect bounds = getBounds();
        LinearGradient gradient = new LinearGradient(bounds.left, bounds.top,
                Math.max(bounds.left + 1, bounds.right), Math.max(bounds.top + 1, bounds.bottom),
                new int[]{base, glow, base}, new float[]{0f, .55f, 1f}, Shader.TileMode.CLAMP);
        gradientPaint.setShader(gradient);
        overlayPaint.setShader(gradient);
    }

    private void updateDestination() {
        if (image == null) return;
        Rect bounds = getBounds();
        float scale = Math.max((float) bounds.width() / image.getWidth(), (float) bounds.height() / image.getHeight());
        float width = image.getWidth() * scale, height = image.getHeight() * scale;
        float left = bounds.exactCenterX() - width / 2f, top = bounds.exactCenterY() - height / 2f;
        destination.set(left, top, left + width, top + height);
    }

    @Override public void draw(Canvas canvas) {
        gradientPaint.setAlpha(alpha);
        canvas.drawRect(getBounds(), gradientPaint);
        if (image != null) {
            imagePaint.setAlpha(Math.round(alpha * intensity));
            canvas.drawBitmap(image, null, destination, imagePaint);
            overlayPaint.setAlpha(Math.round(alpha * (light ? .78f : .68f)));
            canvas.drawRect(getBounds(), overlayPaint);
        }
    }

    @Override public void setAlpha(int value) { alpha = value; invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) {
        gradientPaint.setColorFilter(filter);
        imagePaint.setColorFilter(filter);
        overlayPaint.setColorFilter(filter);
        invalidateSelf();
    }
    @Override public int getOpacity() { return alpha == 255 ? PixelFormat.OPAQUE : PixelFormat.TRANSLUCENT; }
}
