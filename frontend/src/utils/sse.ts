export type SSEHandler = {
  onChunk?: (content: string) => void;
  onSources?: (sources: any[]) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
};

/**
 * 使用 fetch + ReadableStream 解析 SSE 流
 * 后端返回的 SSE 格式为：
 *   data: {"type":"chunk","content":"..."}
 *   data: {"type":"source","sources":[...]}
 *   data: {"type":"done"}
 *   data: {"type":"error","message":"..."}
 */
export async function parseSSEStream(
  response: Response,
  handlers: SSEHandler,
): Promise<void> {
  const { onChunk, onSources, onError, onDone } = handlers;

  if (!response.body) {
    onError?.('响应体为空');
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按行分割
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 保留未完成的行

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue; // 注释行
        if (!trimmed.startsWith('data: ')) continue;

        const jsonStr = trimmed.slice(6);
        try {
          const event = JSON.parse(jsonStr);
          switch (event.type) {
            case 'chunk':
              onChunk?.(event.content);
              break;
            case 'source':
              onSources?.(event.sources);
              break;
            case 'error':
              onError?.(event.message);
              break;
            case 'done':
              onDone?.();
              break;
          }
        } catch {
          // 跳过解析失败的 JSON
        }
      }
    }
  } catch (err) {
    onError?.(`流读取错误: ${err}`);
  } finally {
    reader.releaseLock();
  }
}
