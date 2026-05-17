import 'dart:io';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

const String _kModelFilename = 'islamic_llm_q4_k_m.gguf';

/// Downloads the GGUF model file on first launch and tracks progress.
///
/// Usage:
///   final dl = ModelDownloader();
///   if (!await dl.modelExists()) {
///     await dl.download(
///       url: 'https://huggingface.co/.../islamic_llm_q4_k_m.gguf',
///       onProgress: (pct) => setState(() => _progress = pct),
///     );
///   }
///   final path = await dl.modelPath();
class ModelDownloader {
  final Dio _dio = Dio();
  CancelToken? _cancelToken;

  Future<String> modelPath() async {
    final dir = await getApplicationDocumentsDirectory();
    return '${dir.path}/$_kModelFilename';
  }

  Future<bool> modelExists() async {
    final path = await modelPath();
    return File(path).existsSync();
  }

  /// Downloads the model. [onProgress] receives 0.0–1.0.
  Future<void> download({
    required String url,
    required void Function(double progress) onProgress,
    void Function(String path)? onComplete,
    void Function(Object error)? onError,
  }) async {
    _cancelToken = CancelToken();
    final savePath = await modelPath();

    try {
      await _dio.download(
        url,
        savePath,
        cancelToken: _cancelToken,
        deleteOnError: true,
        onReceiveProgress: (received, total) {
          if (total > 0) {
            onProgress(received / total);
          }
        },
        options: Options(
          receiveTimeout: const Duration(hours: 2),
          headers: {'Accept': 'application/octet-stream'},
        ),
      );
      onComplete?.call(savePath);
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return; // user cancelled — not an error
      onError?.call(e);
    } catch (e) {
      onError?.call(e);
    }
  }

  void cancelDownload() => _cancelToken?.cancel('User cancelled');

  Future<void> deleteModel() async {
    final path = await modelPath();
    final file = File(path);
    if (file.existsSync()) file.deleteSync();
  }

  Future<int> modelSizeBytes() async {
    final path = await modelPath();
    final file = File(path);
    return file.existsSync() ? file.lengthSync() : 0;
  }
}
