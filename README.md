# Email Triage Plugin for Claude

A plugin template that turns Claude into your personal email triage assistant — one who knows which emails need a reply, which just need a glance, and which 47 are noise you can archive without opening.

## What This Is

This is a **plugin** for [Claude](https://claude.ai) (works with both [Cowork](https://claude.ai) and [Claude Code](https://docs.claude.com/en/docs/claude-code)). Once configured, you can say "check my email" and Claude will:

- **Scan your inbox** using Gmail MCP tools (time-windowed, not just unread)
- **Classify every email** into three tiers: Reply Needed, Review, and Noise
- **Draft replies** for the urgent ones, matching your writing style
- **Offer to archive** the noise — with explicit confirmation, never automatically

The triage runs in about 30 seconds for a typical day's inbox. You get a clean summary you can act on instead of scrolling through 200 subject lines.

## Why This Approach

Most inbox management tools try to be clever with rules and auto-sorting. This takes a different approach: Claude actually reads your email (subjects, senders, snippets) and makes judgment calls the way a good executive assistant would.

The key insight is **alias-aware routing**. If you use email aliases — `shopping@yourdomain.com` goes to your inbox but gets a "Shopping" label, `travel@yourdomain.com` gets a "Travel" label — you can map each alias to a default priority tier. A well-configured alias map means 80% of emails get classified instantly, and Claude only needs to read the remaining 20% more carefully.

This pairs especially well with the [Family Assistant Skill](https://github.com/ericporres/family-assistant-skill), which provides the contact context (family members, schools, service providers) that makes triage smarter. But it works standalone too.

## Getting Started

### 1. Install the plugin

**For Cowork users:**
Drop the plugin folder into whichever folder you select when starting a Cowork session.

**For Claude Code users:**
Copy it into your project or home directory:

```bash
cp -r email-triage-plugin ~/.claude/plugins/email-triage-plugin
```

### 2. Connect Gmail

This plugin requires Gmail MCP tools to be available. In Cowork, enable the Gmail connector. In Claude Code, configure the Gmail MCP server.

### 3. Customize the triage rules

Open `skills/email-triage/SKILL.md` and customize:

| Section | What to change |
|---------|---------------|
| **Step 0 — Load Context** | Point to your reference files (family members, aliases, etc.) |
| **Step 1 — Scan Inbox** | Add label exclusions for emails handled elsewhere (e.g., `-label:AI`) |
| **Step 2 — Alias routing** | Map your aliases to default tiers |
| **Step 2 — Urgency signals** | Add your work domain, kids' schools, key contacts |
| **Step 4 — Voice guidelines** | Describe how you write emails so Claude can match your style |

The most impactful customization is the alias routing table in Step 2. If you use 5+ aliases, start there.

### 4. Start using it

```
/email              → Full inbox triage
/email work         → Only work emails
/email personal     → Exclude work emails
/summary            → Alias for /email
```

Or just say:
- *"Check my email"*
- *"What's in my inbox?"*
- *"Catch me up on email from this week"*
- *"Draft a reply to #3"*
- *"Archive the noise"*

## File Structure

```
email-triage-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/
│   ├── email.md             # /email slash command
│   └── summary.md           # /summary alias
├── skills/
│   └── email-triage/
│       └── SKILL.md         # Triage logic, tier definitions, customization points
├── LICENSE
└── README.md
```

## How the Three Tiers Work

**Tier 1 — Reply Needed.** Someone is waiting on you. Family, work, financial alerts, school emails, anything time-sensitive. These are numbered so you can say "draft a reply to #2" and Claude will pull up the full thread, draft something in your voice, and wait for your OK before sending.

**Tier 2 — Review.** Needs your eyes but not a reply. Shipping updates, calendar invites, shared docs, travel confirmations. Presented as a quick-scan list.

**Tier 3 — Noise.** Marketing, social notifications, promotional bulk. Summarized as category counts ("12 marketing, 8 social, 3 automated"). Claude offers to archive them in one shot.

## Tips

**Use email aliases.** This is the single biggest upgrade. If your domain supports catch-all or alias routing, create aliases for categories (`shopping@`, `travel@`, `newsletters@`) and add them to the alias routing table. The triage becomes dramatically more accurate.

**Pair with the Family Assistant.** If Claude knows your family members, their schools, your doctors, and your service providers, it can classify emails from those senders instantly without needing to parse content.

**Run it daily.** The default time window is 24 hours. Running `/email` each morning gives you a clean picture of what came in overnight and what actually needs attention.

**Trust the archive.** Archived emails aren't deleted — they're still searchable. The noise tier is almost always right. Let Claude clear it out.

## What It Doesn't Do

- **Never sends without confirmation.** Claude drafts replies and waits for your explicit "send it."
- **Never auto-archives.** Always asks first, always lists what will be archived.
- **Never deletes.** Archive only. Nothing is permanently removed.
- **Never modifies labels or filters.** Read-only triage.

## Companion Templates

- [Family Assistant Skill](https://github.com/ericporres/family-assistant-skill) — Contact, household, and alias context that makes triage smarter

## Background

This template was built by [Eric Porres](https://github.com/ericporres) after running a personalized version daily for several months. The original handles 150–200 emails a day across 300+ aliases, triaging everything from embassy invitations to wine club promotions. This template abstracts that into a clean starting point anyone can customize.

## License

MIT — use it however you'd like.
