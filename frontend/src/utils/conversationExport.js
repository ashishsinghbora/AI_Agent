function sanitizeFileSegment(value) {
  return String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function normalizeTimestamp(value) {
  if (!value) return new Date().toISOString();
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
}

function normalizeRole(value) {
  const role = String(value || 'assistant').toLowerCase();
  if (role === 'assistant' || role === 'user' || role === 'system') return role;
  return 'assistant';
}

function buildTranscriptMarkdown({ chatMessages, activeQuery, sessionId }) {
  const generatedAt = new Date().toISOString();

  const header = [
    '# Research Assistant Conversation Export',
    '',
    `- Generated At: ${generatedAt}`,
    `- Session ID: ${sessionId || 'unspecified'}`,
    `- Active Query: ${activeQuery || 'unspecified'}`,
    `- Message Count: ${chatMessages.length}`,
    '',
    '## Transcript',
    '',
  ];

  const transcriptBlocks = chatMessages.map((message, index) => {
    const role = normalizeRole(message.role);
    const timestamp = normalizeTimestamp(message.timestamp);
    const content = String(message.content || '').trim() || '(empty)';
    const thinking = String(message.thinking || '').trim();

    const lines = [
      `### ${index + 1}. ${role.toUpperCase()}`,
      `Timestamp: ${timestamp}`,
      '',
      content,
      '',
    ];

    if (thinking) {
      lines.push('```text');
      lines.push('Thinking Notes:');
      lines.push(thinking);
      lines.push('```');
      lines.push('');
    }

    return lines.join('\n');
  });

  return `${header.join('\n')}${transcriptBlocks.join('\n')}`;
}

export function exportConversationTranscript({ chatMessages, activeQuery, sessionId }) {
  if (!Array.isArray(chatMessages) || chatMessages.length === 0) {
    return {
      ok: false,
      message: 'No conversation available to export yet.',
    };
  }

  const markdown = buildTranscriptMarkdown({
    chatMessages,
    activeQuery,
    sessionId,
  });

  const queryPart = sanitizeFileSegment(activeQuery).slice(0, 32) || 'conversation';
  const sessionPart = sanitizeFileSegment(sessionId).slice(0, 22) || 'session';
  const datePart = new Date().toISOString().replace(/[:.]/g, '-');
  const fileName = `research-chat-${queryPart}-${sessionPart}-${datePart}.md`;

  return {
    ok: true,
    fileName,
    content: markdown,
    mimeType: 'text/markdown;charset=utf-8',
  };
}
