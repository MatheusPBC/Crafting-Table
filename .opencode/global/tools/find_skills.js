import fs from "fs"
import path from "path"
import { tool } from "@opencode-ai/plugin"

const CONFIG_DIR = "/home/matheus/.config/opencode"
const GLOBAL_SKILLS_DIR = path.join(CONFIG_DIR, "skills")
const SUPERPOWERS_SKILLS_DIR = path.join(CONFIG_DIR, "superpowers", "skills")

function stripFrontmatter(content) {
  return content.replace(/^---\n[\s\S]*?\n---\n?/, "")
}

function extractFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n?/)
  if (!match) return {}

  const result = {}
  for (const line of match[1].split("\n")) {
    const idx = line.indexOf(":")
    if (idx === -1) continue
    const key = line.slice(0, idx).trim()
    const value = line.slice(idx + 1).trim()
    result[key] = value
  }
  return result
}

function listSkillsFromDir(dir, sourceType) {
  if (!fs.existsSync(dir)) return []

  return fs.readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const skillDir = path.join(dir, entry.name)
      const skillFile = path.join(skillDir, "SKILL.md")
      if (!fs.existsSync(skillFile)) return null
      const content = fs.readFileSync(skillFile, "utf8")
      const frontmatter = extractFrontmatter(content)
      return {
        name: frontmatter.name || entry.name,
        description: frontmatter.description || "",
        path: skillDir,
        sourceType,
      }
    })
    .filter(Boolean)
}

export default tool({
  description: "List globally and project-available skills, including superpowers skills, for reuse across projects.",
  args: {},
  async execute(args, context) {
    const projectSkillsDir = path.join(context.worktree || context.directory, ".opencode", "skills")

    const projectSkills = listSkillsFromDir(projectSkillsDir, "project")
    const globalSkills = listSkillsFromDir(GLOBAL_SKILLS_DIR, "global")
    const superpowersSkills = listSkillsFromDir(SUPERPOWERS_SKILLS_DIR, "superpowers")

    const ordered = [...projectSkills, ...globalSkills, ...superpowersSkills]

    if (ordered.length === 0) {
      return "No skills found."
    }

    const seen = new Set()
    const lines = ["Available skills:", ""]

    for (const skill of ordered) {
      const key = `${skill.sourceType}:${skill.name}`
      if (seen.has(key)) continue
      seen.add(key)

      const prefix = skill.sourceType === "project"
        ? "project:"
        : skill.sourceType === "superpowers"
          ? "superpowers:"
          : ""

      lines.push(`${prefix}${skill.name}`)
      if (skill.description) lines.push(`  ${skill.description}`)
      lines.push(`  Source: ${skill.sourceType}`)
      lines.push(`  Directory: ${skill.path}`)
      lines.push("")
    }

    return lines.join("\n").trim()
  },
})
