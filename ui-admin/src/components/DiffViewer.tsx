import { useMemo } from 'react';
import { html } from 'diff2html';

interface DiffViewerProps {
  baseline: string;
  updated: string;
}

function buildUnifiedDiff(before: string, after: string): string {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');
  const header = ['diff --git a/text b/text', '--- a/text', '+++ b/text'];
  const body: string[] = ['@@ -1,0 +1,0 @@'];
  for (const line of beforeLines) {
    body.push(`-${line}`);
  }
  for (const line of afterLines) {
    body.push(`+${line}`);
  }
  return [...header, ...body].join('\n');
}

const DiffViewer = ({ baseline, updated }: DiffViewerProps) => {
  const diffMarkup = useMemo(() => {
    const diff = buildUnifiedDiff(baseline, updated);
    return html(diff, { drawFileList: false, matching: 'lines', outputFormat: 'line-by-line' });
  }, [baseline, updated]);

  return (
    <div
      className="diff2html text-sm"
      dangerouslySetInnerHTML={{ __html: diffMarkup }}
    />
  );
};

export default DiffViewer;
