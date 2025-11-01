export interface UploadResult {
  runId?: string;
}

export type UploadStatus =
  | { kind: 'idle' }
  | { kind: 'selecting' }
  | { kind: 'uploading'; filename: string }
  | { kind: 'success'; filename: string; runId?: string }
  | { kind: 'error'; filename?: string; message: string };

interface UploadBridge {
  ingestDataFile?: (file: File) => Promise<UploadResult | void> | UploadResult | void;
  ingestBlueprint?: (file: File) => Promise<UploadResult | void> | UploadResult | void;
}

declare global {
  interface Window {
    __YOSAI_UPLOAD__?: UploadBridge;
  }
}

function getUploadBridge(): UploadBridge | undefined {
  if (typeof window === 'undefined') {
    return undefined;
  }
  return window.__YOSAI_UPLOAD__;
}

async function invokeHandler(
  handler: ((file: File) => Promise<UploadResult | void> | UploadResult | void) | undefined,
  file: File,
): Promise<UploadResult | void> {
  if (!handler) {
    return undefined;
  }

  return await handler(file);
}

export async function ingestDataFile(file: File): Promise<UploadResult | void> {
  const bridge = getUploadBridge();
  return invokeHandler(bridge?.ingestDataFile, file);
}

export async function ingestBlueprint(file: File): Promise<UploadResult | void> {
  const bridge = getUploadBridge();
  return invokeHandler(bridge?.ingestBlueprint, file);
}
