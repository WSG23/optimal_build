// Lightweight, optional bridge so we never break existing upload flows.
// If the host app defines window.__YOSAI_UPLOAD__ handlers, we forward to them.
// Otherwise these become safe no-ops with status callbacks.

export type UploadStatus =
  | { kind: 'idle' }
  | { kind: 'selecting' }
  | { kind: 'uploading'; filename: string }
  | { kind: 'success'; filename: string; runId?: string }
  | { kind: 'error'; filename?: string; message: string };

type UploadHandlers = {
  ingestDataFile?: (file: File) => Promise<{ runId?: string } | void>;
  ingestBlueprint?: (file: File) => Promise<{ schemaVersionId?: string } | void>;
};

declare global {
  interface Window {
    __YOSAI_UPLOAD__?: UploadHandlers;
  }
}

const getHandlers = (): UploadHandlers => {
  if (typeof window !== 'undefined' && window.__YOSAI_UPLOAD__) {
    return window.__YOSAI_UPLOAD__;
  }
  return {};
};

export async function ingestDataFile(
  file: File,
  onStatus?: (s: UploadStatus) => void,
): Promise<void> {
  onStatus?.({ kind: 'uploading', filename: file.name });
  try {
    const { ingestDataFile } = getHandlers();
    const result = ingestDataFile ? await ingestDataFile(file) : undefined;
    const runId = result && typeof result === 'object' ? result.runId : undefined;
    onStatus?.({ kind: 'success', filename: file.name, runId });
  } catch (error: unknown) {
    const message = (error as { message?: string } | undefined)?.message ?? 'Upload failed';
    onStatus?.({
      kind: 'error',
      filename: file.name,
      message,
    });
  }
}

export async function ingestBlueprint(
  file: File,
  onStatus?: (s: UploadStatus) => void,
): Promise<void> {
  onStatus?.({ kind: 'uploading', filename: file.name });
  try {
    const { ingestBlueprint } = getHandlers();
    const result = ingestBlueprint ? await ingestBlueprint(file) : undefined;
    const runId = result && typeof result === 'object' ? result.schemaVersionId : undefined;
    onStatus?.({
      kind: 'success',
      filename: file.name,
      runId,
    });
  } catch (error: unknown) {
    const message = (error as { message?: string } | undefined)?.message ?? 'Upload failed';
    onStatus?.({
      kind: 'error',
      filename: file.name,
      message,
    });
  }
}
