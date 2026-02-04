---
name: flutter-image-caching
description: Image caching and optimization in Flutter
applies_to: flutter
---

# Flutter Image Caching

## Overview

Efficient image handling is crucial for Flutter app performance. This covers caching strategies, memory management, and optimization techniques.

## Dependencies

```yaml
dependencies:
  cached_network_image: ^3.3.1
  flutter_cache_manager: ^3.3.1
  extended_image: ^8.2.0
```

## CachedNetworkImage

### Basic Usage

```dart
import 'package:cached_network_image/cached_network_image.dart';

class ProductImage extends StatelessWidget {
  final String imageUrl;

  const ProductImage({required this.imageUrl, super.key});

  @override
  Widget build(BuildContext context) {
    return CachedNetworkImage(
      imageUrl: imageUrl,
      placeholder: (context, url) => const CircularProgressIndicator(),
      errorWidget: (context, url, error) => const Icon(Icons.error),
    );
  }
}
```

### With Custom Placeholder

```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  placeholder: (context, url) => Container(
    color: Colors.grey[200],
    child: const Center(
      child: Icon(Icons.image, size: 40, color: Colors.grey),
    ),
  ),
  errorWidget: (context, url, error) => Container(
    color: Colors.grey[200],
    child: const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.error_outline, size: 40, color: Colors.red),
          SizedBox(height: 8),
          Text('Failed to load image'),
        ],
      ),
    ),
  ),
  fit: BoxFit.cover,
)
```

### With Shimmer Effect

```dart
import 'package:shimmer/shimmer.dart';

CachedNetworkImage(
  imageUrl: imageUrl,
  placeholder: (context, url) => Shimmer.fromColors(
    baseColor: Colors.grey[300]!,
    highlightColor: Colors.grey[100]!,
    child: Container(
      color: Colors.white,
    ),
  ),
  errorWidget: (context, url, error) => const ErrorPlaceholder(),
  fit: BoxFit.cover,
)
```

### With Fade Animation

```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  fadeInDuration: const Duration(milliseconds: 300),
  fadeOutDuration: const Duration(milliseconds: 100),
  fadeInCurve: Curves.easeIn,
  fadeOutCurve: Curves.easeOut,
  placeholder: (context, url) => const ColoredBox(color: Colors.grey),
  fit: BoxFit.cover,
)
```

## Custom Cache Manager

```dart
import 'package:flutter_cache_manager/flutter_cache_manager.dart';

class CustomCacheManager {
  static const key = 'customCacheKey';

  static CacheManager instance = CacheManager(
    Config(
      key,
      stalePeriod: const Duration(days: 7),
      maxNrOfCacheObjects: 100,
      repo: JsonCacheInfoRepository(databaseName: key),
      fileService: HttpFileService(),
    ),
  );
}

// Usage
CachedNetworkImage(
  imageUrl: imageUrl,
  cacheManager: CustomCacheManager.instance,
)
```

### Multiple Cache Managers

```dart
class ImageCacheManagers {
  // Cache for product images (longer retention)
  static CacheManager productImages = CacheManager(
    Config(
      'productImages',
      stalePeriod: const Duration(days: 30),
      maxNrOfCacheObjects: 200,
    ),
  );

  // Cache for user avatars (medium retention)
  static CacheManager avatars = CacheManager(
    Config(
      'avatars',
      stalePeriod: const Duration(days: 7),
      maxNrOfCacheObjects: 100,
    ),
  );

  // Cache for thumbnails (short retention)
  static CacheManager thumbnails = CacheManager(
    Config(
      'thumbnails',
      stalePeriod: const Duration(days: 1),
      maxNrOfCacheObjects: 500,
    ),
  );

  // Clear all caches
  static Future<void> clearAll() async {
    await productImages.emptyCache();
    await avatars.emptyCache();
    await thumbnails.emptyCache();
  }
}

// Usage
CachedNetworkImage(
  imageUrl: productUrl,
  cacheManager: ImageCacheManagers.productImages,
)

CachedNetworkImage(
  imageUrl: avatarUrl,
  cacheManager: ImageCacheManagers.avatars,
)
```

## Memory-Efficient Image Loading

### Resize Images on Load

```dart
// Using cacheWidth and cacheHeight to resize
Image.network(
  imageUrl,
  cacheWidth: 400, // Decoded image width
  cacheHeight: 400, // Decoded image height
)

// With CachedNetworkImage
CachedNetworkImage(
  imageUrl: imageUrl,
  memCacheWidth: 400,
  memCacheHeight: 400,
  maxWidthDiskCache: 800,
  maxHeightDiskCache: 800,
)
```

### Responsive Image Sizing

```dart
class ResponsiveImage extends StatelessWidget {
  final String imageUrl;

  const ResponsiveImage({required this.imageUrl, super.key});

  @override
  Widget build(BuildContext context) {
    final devicePixelRatio = MediaQuery.of(context).devicePixelRatio;
    final screenWidth = MediaQuery.of(context).size.width;

    // Calculate optimal cache size based on screen
    final cacheWidth = (screenWidth * devicePixelRatio).round();

    return CachedNetworkImage(
      imageUrl: imageUrl,
      memCacheWidth: cacheWidth,
      fit: BoxFit.cover,
    );
  }
}
```

### Progressive Image Loading

```dart
class ProgressiveImage extends StatelessWidget {
  final String thumbnailUrl;
  final String fullUrl;

  const ProgressiveImage({
    required this.thumbnailUrl,
    required this.fullUrl,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        // Low-res thumbnail (loads fast)
        CachedNetworkImage(
          imageUrl: thumbnailUrl,
          fit: BoxFit.cover,
        ),
        // Full resolution (fades in when loaded)
        CachedNetworkImage(
          imageUrl: fullUrl,
          fit: BoxFit.cover,
          fadeInDuration: const Duration(milliseconds: 500),
          placeholder: (_, __) => const SizedBox.shrink(),
        ),
      ],
    );
  }
}
```

## Extended Image (Advanced Features)

```dart
import 'package:extended_image/extended_image.dart';

class AdvancedImage extends StatelessWidget {
  final String imageUrl;

  const AdvancedImage({required this.imageUrl, super.key});

  @override
  Widget build(BuildContext context) {
    return ExtendedImage.network(
      imageUrl,
      cache: true,
      fit: BoxFit.cover,
      loadStateChanged: (state) {
        switch (state.extendedImageLoadState) {
          case LoadState.loading:
            return const Center(child: CircularProgressIndicator());
          case LoadState.completed:
            return ExtendedRawImage(
              image: state.extendedImageInfo?.image,
              fit: BoxFit.cover,
            );
          case LoadState.failed:
            return GestureDetector(
              onTap: () => state.reLoadImage(),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.error),
                    Text('Tap to retry'),
                  ],
                ),
              ),
            );
        }
      },
    );
  }
}
```

### Image with Zoom

```dart
ExtendedImage.network(
  imageUrl,
  mode: ExtendedImageMode.gesture,
  initGestureConfigHandler: (state) {
    return GestureConfig(
      minScale: 0.9,
      maxScale: 3.0,
      animationMinScale: 0.7,
      animationMaxScale: 3.5,
      speed: 1.0,
      inertialSpeed: 100.0,
      initialScale: 1.0,
      inPageView: false,
      initialAlignment: InitialAlignment.center,
    );
  },
)
```

### Image Editor

```dart
class ImageEditorWidget extends StatefulWidget {
  final String imageUrl;

  const ImageEditorWidget({required this.imageUrl, super.key});

  @override
  State<ImageEditorWidget> createState() => _ImageEditorWidgetState();
}

class _ImageEditorWidgetState extends State<ImageEditorWidget> {
  final GlobalKey<ExtendedImageEditorState> _editorKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: ExtendedImage.network(
            widget.imageUrl,
            fit: BoxFit.contain,
            mode: ExtendedImageMode.editor,
            extendedImageEditorKey: _editorKey,
            initEditorConfigHandler: (state) {
              return EditorConfig(
                maxScale: 8.0,
                cropRectPadding: const EdgeInsets.all(20.0),
                hitTestSize: 20.0,
                cropAspectRatio: CropAspectRatios.ratio1_1,
              );
            },
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            IconButton(
              icon: const Icon(Icons.rotate_left),
              onPressed: () {
                _editorKey.currentState?.rotate(right: false);
              },
            ),
            IconButton(
              icon: const Icon(Icons.rotate_right),
              onPressed: () {
                _editorKey.currentState?.rotate(right: true);
              },
            ),
            IconButton(
              icon: const Icon(Icons.flip),
              onPressed: () {
                _editorKey.currentState?.flip();
              },
            ),
            IconButton(
              icon: const Icon(Icons.check),
              onPressed: () async {
                final cropRect = _editorKey.currentState?.getCropRect();
                // Process cropped image
              },
            ),
          ],
        ),
      ],
    );
  }
}
```

## Precaching Images

```dart
class ImagePrecacher {
  // Precache single image
  static Future<void> precache(BuildContext context, String url) async {
    await precacheImage(
      CachedNetworkImageProvider(url),
      context,
    );
  }

  // Precache multiple images
  static Future<void> precacheAll(
    BuildContext context,
    List<String> urls,
  ) async {
    await Future.wait(
      urls.map((url) => precacheImage(
            CachedNetworkImageProvider(url),
            context,
          )),
    );
  }

  // Precache with progress
  static Stream<double> precacheWithProgress(
    BuildContext context,
    List<String> urls,
  ) async* {
    var completed = 0;

    for (final url in urls) {
      await precacheImage(
        CachedNetworkImageProvider(url),
        context,
      );
      completed++;
      yield completed / urls.length;
    }
  }
}

// Usage in initState or when data loads
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ImagePrecacher.precacheAll(context, [
      product.imageUrl,
      product.thumbnailUrl,
      ...product.galleryUrls,
    ]);
  });
}
```

## Image Provider Pattern

```dart
class OptimizedImageProvider {
  final String baseUrl;
  final CacheManager cacheManager;

  OptimizedImageProvider({
    required this.baseUrl,
    CacheManager? cacheManager,
  }) : cacheManager = cacheManager ?? DefaultCacheManager();

  // Generate URL with size parameters
  String getUrl(String imagePath, {int? width, int? height}) {
    final params = <String>[];
    if (width != null) params.add('w=$width');
    if (height != null) params.add('h=$height');

    final queryString = params.isNotEmpty ? '?${params.join('&')}' : '';
    return '$baseUrl$imagePath$queryString';
  }

  // Get thumbnail
  String getThumbnail(String imagePath) {
    return getUrl(imagePath, width: 200, height: 200);
  }

  // Get full size
  String getFullSize(String imagePath) {
    return getUrl(imagePath);
  }

  // Widget builder
  Widget buildImage(
    String imagePath, {
    BoxFit fit = BoxFit.cover,
    int? width,
    int? height,
  }) {
    return CachedNetworkImage(
      imageUrl: getUrl(imagePath, width: width, height: height),
      cacheManager: cacheManager,
      fit: fit,
      placeholder: (_, __) => const ImagePlaceholder(),
      errorWidget: (_, __, ___) => const ImageErrorWidget(),
    );
  }
}

// Usage
final imageProvider = OptimizedImageProvider(
  baseUrl: 'https://cdn.example.com/images/',
);

// In widget
imageProvider.buildImage('products/123.jpg', width: 400, height: 400)
```

## Cache Management

```dart
class ImageCacheService {
  final CacheManager _cacheManager;

  ImageCacheService({CacheManager? cacheManager})
      : _cacheManager = cacheManager ?? DefaultCacheManager();

  // Get cache size
  Future<int> getCacheSize() async {
    final store = await _cacheManager.store;
    // Note: Actual implementation depends on cache manager
    return 0; // Placeholder
  }

  // Clear entire cache
  Future<void> clearCache() async {
    await _cacheManager.emptyCache();
  }

  // Remove single file from cache
  Future<void> removeFromCache(String url) async {
    await _cacheManager.removeFile(url);
  }

  // Download and cache image
  Future<File> downloadAndCache(String url) async {
    return _cacheManager.getSingleFile(url);
  }

  // Check if image is cached
  Future<bool> isCached(String url) async {
    final file = await _cacheManager.getFileFromCache(url);
    return file != null;
  }
}
```

## Placeholder Widgets

```dart
class ImagePlaceholder extends StatelessWidget {
  final double? width;
  final double? height;

  const ImagePlaceholder({this.width, this.height, super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      color: Colors.grey[200],
      child: const Center(
        child: Icon(Icons.image, color: Colors.grey),
      ),
    );
  }
}

class ImageErrorWidget extends StatelessWidget {
  final VoidCallback? onRetry;

  const ImageErrorWidget({this.onRetry, super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.grey[200],
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.broken_image, color: Colors.grey),
            if (onRetry != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: onRetry,
                child: const Text('Retry'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

## Image Gallery with Caching

```dart
class CachedImageGallery extends StatelessWidget {
  final List<String> imageUrls;
  final int initialIndex;

  const CachedImageGallery({
    required this.imageUrls,
    this.initialIndex = 0,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: PageView.builder(
        controller: PageController(initialPage: initialIndex),
        itemCount: imageUrls.length,
        itemBuilder: (context, index) {
          return InteractiveViewer(
            minScale: 0.5,
            maxScale: 4.0,
            child: Center(
              child: CachedNetworkImage(
                imageUrl: imageUrls[index],
                fit: BoxFit.contain,
                placeholder: (_, __) => const CircularProgressIndicator(
                  color: Colors.white,
                ),
                errorWidget: (_, __, ___) => const Icon(
                  Icons.error,
                  color: Colors.white,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
```

## Best Practices

1. **Always use caching** - Avoid re-downloading images
2. **Resize images** - Use cacheWidth/cacheHeight for memory efficiency
3. **Show placeholders** - Improve perceived performance
4. **Handle errors** - Provide retry options and fallbacks
5. **Precache when possible** - Load important images ahead of time
6. **Use appropriate cache duration** - Balance storage vs freshness
7. **Clear cache periodically** - Prevent excessive storage use
8. **Use CDN URLs** - Leverage server-side image optimization
