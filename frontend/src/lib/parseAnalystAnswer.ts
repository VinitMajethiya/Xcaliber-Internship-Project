/**
 * Parses the 3-part analyst response structure (Direct Answer, Supporting Numbers, Strategic Takeaway)
 * from the assistant's synthesized markdown response.
 */
export interface AnalystSections {
  finding: string;
  metrics: string;
  whyItMatters: string;
  isStructured: boolean;
}

export function parseAnalystAnswer(markdown: string): AnalystSections {
  if (!markdown) {
    return { finding: '', metrics: '', whyItMatters: '', isStructured: false };
  }

  const sections = { finding: '', metrics: '', whyItMatters: '' };

  // Support both "### Direct Answer" and "**1. Direct Answer:**" / "# Direct Answer" patterns
  const parts = markdown.split(/(?:^|\n)###?\s+|\n(?=\*\*(?:[1-3]\.\s*)?[A-Za-z\s]+:\*\*)/g).filter(Boolean);

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    // Check if part starts with bold header like **1. Direct Answer:**
    let headerLine = '';
    let body = '';

    if (trimmed.startsWith('**')) {
      const closingIdx = trimmed.indexOf('**', 2);
      if (closingIdx !== -1) {
        headerLine = trimmed.substring(2, closingIdx);
        body = trimmed.substring(closingIdx + 2).replace(/^:\s*/, '').trim();
      }
    } else {
      const newlineIdx = trimmed.indexOf('\n');
      if (newlineIdx !== -1) {
        headerLine = trimmed.substring(0, newlineIdx);
        body = trimmed.substring(newlineIdx + 1).trim();
      } else {
        headerLine = trimmed;
      }
    }

    const header = headerLine.toLowerCase();

    if (header.includes('direct answer') || header.includes('executive insight') || header.includes('finding')) {
      sections.finding = body;
    } else if (header.includes('supporting') || header.includes('numbers') || header.includes('breakdown')) {
      sections.metrics = body;
    } else if (header.includes('takeaway') || header.includes('matters') || header.includes('strategic') || header.includes('implication')) {
      sections.whyItMatters = body;
    }
  }

  const isStructured = Boolean(
    sections.finding && (sections.metrics || sections.whyItMatters)
  );

  if (!isStructured) {
    sections.finding = markdown;
  }

  return {
    ...sections,
    isStructured,
  };
}
