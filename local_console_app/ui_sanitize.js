function normalizeVisibleText(text) {
  return String(text || '')
    .replace(/Stage\d+/gi, '统一模块')
    .replace(/stage\d+/gi, 'unified')
    .replace(/local_console_[A-Za-z0-9_\-]+/g, '统一控制台产物');
}

function sanitizeVisibleNode(node) {
  if (!node) return;
  if (node.nodeType === Node.TEXT_NODE) {
    const next = normalizeVisibleText(node.nodeValue);
    if (next !== node.nodeValue) node.nodeValue = next;
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;
  if (['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT'].includes(node.tagName)) return;
  for (const child of node.childNodes) sanitizeVisibleNode(child);
}

const visibleTextObserver = new MutationObserver(() => sanitizeVisibleNode(document.body));
visibleTextObserver.observe(document.documentElement, {childList: true, subtree: true, characterData: true});
document.addEventListener('DOMContentLoaded', () => sanitizeVisibleNode(document.body));
