// Activepieces Code Step: Clean Unread Emails & Handle Zero Inbox
export const code = async (inputs) => {
  const emails = inputs.messages || [];

  if (!emails || emails.length === 0) {
    return {
      has_unread: false,
      count: 0,
      clean_text: "🎉 *Inbox Zero!*\nYou have no unread emails right now."
    };
  }

  const formatted = emails.map((m, i) => {
    const from = m.from || "Unknown";
    const subject = m.subject || "No Subject";
    const date = m.date || "";
    // Clean snippet removing excess line breaks & tags
    const snippet = (m.snippet || m.body || "")
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 250);

    return `[#${i + 1}] From: ${from}\nSubject: ${subject}\nTime: ${date}\nPreview: ${snippet}`;
  }).join("\n\n---\n\n");

  return {
    has_unread: true,
    count: emails.length,
    clean_text: formatted
  };
};
