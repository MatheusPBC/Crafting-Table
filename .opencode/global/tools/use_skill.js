import fs from "fs"
import path from "path"
import { tool } from "@opencode-ai/plugin"

const CONFIG_DIR = "/home/matheus/.config/opencode"
const GLOBAL_SKILLS_DIR = path.join(CONFIG_DIR, "skills")
const SUPERPOWERS_SKILLS_DIR = path.join(CONFIG_DIR, "superpowers", "skills")

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

function stripFrontmatter(content) {
  return content.replace(/^---\n[\s\S]*?\n---\n?/, "")
}

function resolveSkill(skillName, context) {
  const projectSkillsDir = path.join(context.worktree || context.directory, ".opencode", "skills")
  const forceProject = skillName.startsWith("project:")
  const forceSuperpowers = skillName.startsWith("superpowers:")
  const baseName = skillName.replace(/^project:/, "").replace(/^superpowers:/, "")

  const candidates = []
  if (forceProject) {
    candidates.push(path.join(projectSkillsDir, baseName, "SKILL.md"))
  } else if (forceSuperpowers) {
    candidates.push(path.join(SUPERPOWERS_SKILLS_DIR, baseName, "SKILL.md"))
  } else {
    candidates.push(path.join(projectSkillsDir, baseName, "SKILL.md"))
    candidates.push(path.join(GLOBAL_SKILLS_DIR, baseName, "SKILL.md"))
    candidates.push(path.join(SUPERPOWERS_SKILLS_DIR, baseName, "SKILL.md"))
  }

  for (const file of candidates) {
    if (fs.existsSync(file)) return file
  }

  return null
}

export default tool({
  description: "Load the contents of a global, project, or superpowers skill and return it directly to the model.",
  args: {
    skill_name: tool.schema.string().describe("Skill name, for example clean-code, project:my-skill, or superpowers:brainstorming"),
  },
  async execute(args, context) {
    const skillFile = resolveSkill(args.skill_name, context)
    if (!skillFile) {
      return `Skill not found: ${args.skill_name}\n\nUse find_skills to list available skills.`
    }

    const raw = fs.readFileSync(skillFile, "utf8")
    const meta = extractFrontmatter(raw)
    const body = stripFrontmatter(raw)

    return [
      `# ${meta.name || args.skill_name}`,
      meta.description ? `# ${meta.description}` : "",
      `# Path: ${skillFile}`,
      "# ============================================",
      "",
      body.trim(),
    ].filter(Boolean).join("\n")
  },
})
