import React, { useState } from 'react';
import './DiffViewer.css';

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'context';
  content: string;
  lineNumber: number;
  originalLineNumber?: number;
}

interface FileDiff {
  filePath: string;
  status: 'created' | 'modified' | 'deleted';
  original: string;
  modified: string;
  diffLines: DiffLine[];
}

interface DiffViewerProps {
  diffs: FileDiff[];
  onAccept?: (filePath: string) => void;
  onReject?: (filePath: string) => void;
  onAcceptAll?: () => void;
  onRejectAll?: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  diffs,
  onAccept,
  onReject,
  onAcceptAll,
  onRejectAll,
}) => {
  const [activeDiff, setActiveDiff] = useState(diffs.length > 0 ? diffs[0].filePath : null);
  const [fileStatuses, setFileStatuses] = useState<Record<string, 'pending' | 'accepted' | 'rejected'>>(
    Object.fromEntries(diffs.map(d => [d.filePath, 'pending']))
  );

  if (diffs.length === 0) {
    return (
      <div className="diff-viewer empty">
        <p>No diffs to display</p>
      </div>
    );
  }

  const currentDiff = diffs.find(d => d.filePath === activeDiff);
  if (!currentDiff) return null;

  const handleAccept = (filePath: string) => {
    setFileStatuses(prev => ({ ...prev, [filePath]: 'accepted' }));
    onAccept?.(filePath);
  };

  const handleReject = (filePath: string) => {
    setFileStatuses(prev => ({ ...prev, [filePath]: 'rejected' }));
    onReject?.(filePath);
  };

  const acceptedCount = Object.values(fileStatuses).filter(s => s === 'accepted').length;
  const rejectedCount = Object.values(fileStatuses).filter(s => s === 'rejected').length;

  return (
    <div className="diff-viewer">
      <div className="diff-toolbar">
        <div className="tabs">
          {diffs.map(diff => (
            <button
              key={diff.filePath}
              className={`tab ${activeDiff === diff.filePath ? 'active' : ''} ${fileStatuses[diff.filePath]}`}
              onClick={() => setActiveDiff(diff.filePath)}
              title={diff.filePath}
            >
              <span className="status-icon">
                {fileStatuses[diff.filePath] === 'accepted' && '✓'}
                {fileStatuses[diff.filePath] === 'rejected' && '✗'}
              </span>
              <span className="filename">{diff.filePath.split('/').pop()}</span>
              <span className="badge">
                {diff.status === 'created' && 'new'}
                {diff.status === 'modified' && 'modified'}
                {diff.status === 'deleted' && 'deleted'}
              </span>
            </button>
          ))}
        </div>

        <div className="toolbar-actions">
          <span className="stats">
            {acceptedCount}/{diffs.length} accepted
          </span>
          <button
            className="action-button accept-all"
            onClick={onAcceptAll}
            title="Accept all changes"
          >
            ✓ Accept All
          </button>
          <button
            className="action-button reject-all"
            onClick={onRejectAll}
            title="Reject all changes"
          >
            ✗ Reject All
          </button>
        </div>
      </div>

      {currentDiff && (
        <div className="diff-content">
          <div className="file-header">
            <div className="file-info">
              <span className={`status ${currentDiff.status}`}>
                {currentDiff.status === 'created' && '+ Created'}
                {currentDiff.status === 'modified' && '~ Modified'}
                {currentDiff.status === 'deleted' && '- Deleted'}
              </span>
              <span className="filepath">{currentDiff.filePath}</span>
            </div>
            <div className="file-actions">
              <button
                className="btn-accept"
                onClick={() => handleAccept(currentDiff.filePath)}
                disabled={fileStatuses[currentDiff.filePath] === 'accepted'}
              >
                ✓ Accept
              </button>
              <button
                className="btn-reject"
                onClick={() => handleReject(currentDiff.filePath)}
                disabled={fileStatuses[currentDiff.filePath] === 'rejected'}
              >
                ✗ Reject
              </button>
            </div>
          </div>

          <div className="diff-lines">
            {currentDiff.diffLines.map((line, idx) => (
              <div key={idx} className={`diff-line line-${line.type}`}>
                <span className="line-number">{line.lineNumber}</span>
                <span className="diff-marker">
                  {line.type === 'added' && '+'}
                  {line.type === 'removed' && '-'}
                  {line.type === 'unchanged' && ' '}
                  {line.type === 'context' && ' '}
                </span>
                <code className="line-content">{line.content}</code>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Parse unified diff format to DiffLine[]
 * Used to convert raw diffs from backend into DiffViewer format
 */
export const parseDiffLines = (diffText: string): DiffLine[] => {
  const lines = diffText.split('\n');
  const result: DiffLine[] = [];
  let lineNumber = 0;

  for (const line of lines) {
    if (line.startsWith('+') && !line.startsWith('+++')) {
      result.push({
        type: 'added',
        content: line.slice(1),
        lineNumber: ++lineNumber,
      });
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      result.push({
        type: 'removed',
        content: line.slice(1),
        lineNumber,
      });
    } else if (line.startsWith('@@')) {
      // Extract line number from @@ -old,count +new,count @@
      const match = line.match(/@@ -\d+(?:,\d+)? \+(\d+)/);
      if (match) {
        lineNumber = parseInt(match[1], 10) - 1;
      }
    } else if (!line.startsWith('---') && !line.startsWith('+++')) {
      result.push({
        type: 'unchanged',
        content: line,
        lineNumber: ++lineNumber,
      });
    }
  }

  return result;
};
