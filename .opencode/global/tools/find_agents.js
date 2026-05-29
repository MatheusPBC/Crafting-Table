import fs from "fs"
import path from "path"
import { tool } from "@opencode-ai/plugin"

const CONFIG_DIR = "/home/matheus/.config/opencode"
const GLOBAL_AGENTS_DIR = path.join(CONFIG_DIR, "agents")

function extractFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n?/)
  if (!match) return {}

  const result = {}
  for (const line of match[1].split("\n")) {
    const idx = line.indexOf(":")
    if (idx === -1) continue
    result[line.slice(0, idx).trim()] = line.slice(idx + 1).trim().replace(/^"|"$/g, "")
  }
  return result
}

function listAgents(dir, sourceType) {
  if (!fs.existsSync(dir)) return []

  return fs.readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
    .map((entry) => {
      const file = path.join(dir, entry.name)
      const meta = extractFrontmatter(fs.readFileSync(file, "utf8"))
      return {
        name: entry.name.replace(/\.md$/, ""),
        description: meta.description || "",
        mode: meta.mode || "",
        path: file,
        sourceType,
      }
    })
}

export default tool({
  description: "List project and global OpenCode agents with descriptions.",
  args: {},
  async execute(args, context) {
    const projectDir = path.join(context.worktree || context.directory, ".opencode", "agents")
    const items = [...listAgents(projectDir, "project"), ...listAgents(GLOBAL_AGENTS_DIR, "global")]

    if (!items.length) return "No custom agents found."

    const lines = ["Available custom agents:", ""]
    for (const item of items) {
      lines.push(item.name)
      if (item.description) lines.push(`  ${item.description}`)
      if (item.mode) lines.push(`  Mode: ${item.mode}`)
      lines.push(`  Source: ${item.sourceType}`)
      lines.push(`  Path: ${item.path}`)
      lines.push("")
    }
    return lines.join("\n").trim()
  },
})
