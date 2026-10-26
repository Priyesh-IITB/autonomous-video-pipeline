# Source of truth for this video's script.json. Every fact maps to sources.md.
import json, os
SRC_THN = "Source: The Hacker News, Sep 9 2026"
def src(s): return f"<div class='source'>{s}</div>"
B = []
def beat(id, say, html, chapter=None, css=""):
    B.append({"id": id, "say": " ".join(say.split()), "html": html, "chapter": chapter, "css": css})

beat("b01", """Before you trust your agent's sandbox, look at how a 9.4 critical bug let DeepSeek Harness
agents turn theirs off.""",
"""<div class='stage'><div class='kicker bad in'>CVE-2026-82533 · DeepSeek Harness</div>
<div class='row' style='align-items:center'><h1 class='in d1' style='flex:1.6'>The agent turned off its own <span class='bad'>sandbox</span>.</h1>
<div class='pop d4' style='flex:1;text-align:center'><div class='big-num bad'>9.4</div><div class='pill bad' style='margin-top:20px'>CRITICAL</div></div></div></div>"""
+ src("Source: VulnCheck CVSS 4.0, via NVD"), chapter="The bug")

beat("b02", """Your coding agent asks before it does anything risky. But in DeepSeek Harness, it could stop
asking, and the log said you approved it. In this video, I'll show you exactly how that worked, what the fix
changed, and what it did not change.""",
"""<div class='stage'><div class='row'>
<div class='box good in'><div class='kicker'>Expected</div><p style='margin-top:20px'>Agent: <i>"Can I write outside the project?"</i></p><p class='accent' style='margin-top:14px'>You: approve / deny</p></div>
<div class='box bad in d4'><div class='kicker bad'>What happened</div><p style='margin-top:20px'>Agent changed its own permissions.</p><p class='bad' style='margin-top:14px'>Log: "changed by user"</p></div>
</div><ul style='margin-top:30px'><li class='in d8'>How it worked</li><li class='in d9'>What the fix changed</li><li class='in d10'>What it <span class='bad'>didn't</span></li></ul></div>"""
+ src("Source: Forkast; The Hacker News"))

beat("b03", """If we take a step back, DeepSeek Harness, or dsh, is DeepSeek's open-source agent harness. MIT
licensed, everything is a plugin, and it actually has more than two hundred and fifty thousand stars on GitHub.
You start it with one npx command, and it serves a web UI on your own machine, on port 3080.""",
"""<div class='stage'><div class='kicker info in'>What dsh is</div><h2 class='in d1'>DeepSeek Harness</h2>
<div class='row in d3'><div class='box'><h3>Licence</h3><p>MIT, open source</p></div><div class='box'><h3>Design</h3><p>Everything is a plugin</p></div><div class='box'><h3>GitHub</h3><p>~257k stars</p></div></div>
<div class='term in d6'><span class='prompt'>$</span> npx @deepseek-ai/dsh web<br><span class='muted'>→ Web UI at http://127.0.0.1:3080</span></div></div>"""
+ src("Source: github.com/deepseek-ai/deepseek-harness"), chapter="What dsh is")

beat("b04", """The agent runs inside a sandbox with three modes. Read-only. Workspace-write, where it can only
write inside your project. And danger-full-access, where there is no confinement at all. But notice one thing
from the docs. These modes cover file writes. Network is outside this vocabulary.""",
"""<div class='stage'><div class='kicker info in'>Sandbox modes</div><div class='row'>
<div class='box good in d1'><h3>read-only</h3><p>No writes</p></div>
<div class='box in d3' style='border-color:var(--warn)'><h3>workspace-write</h3><p>Writes inside the project</p></div>
<div class='box bad in d5'><h3>danger-full-access</h3><p>No confinement</p></div></div>
<div class='box in d9' style='margin-top:20px'><p class='mono' style='font-size:38px'>"Network and process visibility are outside this vocabulary."</p></div></div>"""
+ src("Source: dsh docs, subsystems/sandbox.md"))

FLOW = """<svg viewBox='0 0 1640 360' width='1640' height='360' style='display:block'>
<defs><marker id='a' markerWidth='12' markerHeight='12' refX='10' refY='6' orient='auto'><path d='M0,0 L12,6 L0,12 z' fill='#8b97ab'/></marker></defs>
<g font-family='Inter' font-size='34' font-weight='700' fill='#e8ecf3' text-anchor='middle'>
<rect x='10' y='110' width='330' height='140' rx='20' fill='#131a26' stroke='#243044' stroke-width='3'/><text x='175' y='170'>Agent shell</text><text x='175' y='215' font-size='26' fill='#8b97ab' font-weight='500'>inside sandbox</text>
<rect x='650' y='110' width='340' height='140' rx='20' fill='#131a26' stroke='#f87171' stroke-width='3'/><text x='820' y='170'>Control API</text><text x='820' y='215' font-size='26' fill='#f87171' font-weight='500'>127.0.0.1 · no auth</text>
<rect x='1290' y='110' width='340' height='140' rx='20' fill='#131a26' stroke='#f87171' stroke-width='3'/><text x='1460' y='170'>Session mode</text><text x='1460' y='215' font-size='26' fill='#f87171' font-weight='500'>danger-full-access</text></g>
<path class='draw d2' d='M345,180 L640,180' stroke='#8b97ab' stroke-width='5' fill='none' marker-end='url(#a)'/>
<path class='draw d5' d='M995,180 L1280,180' stroke='#8b97ab' stroke-width='5' fill='none' marker-end='url(#a)'/>
<text class='in d3' x='492' y='150' font-family='Inter' font-size='26' fill='#fbbf24' text-anchor='middle'>loopback is open</text>
<text class='in d6' x='1137' y='150' font-family='Inter' font-size='26' fill='#fbbf24' text-anchor='middle'>one call</text></svg>"""

beat("b05", """And that is the whole bug. The web UI is controlled by a local API. That API had no
authentication. It only checked the Host header, which the caller can simply set. The code comment even says it
is not an auth layer.""",
"""<div class='stage'><div class='kicker bad in'>The bug</div><h2 class='in d1'>A local control API with <span class='bad'>no authentication</span></h2>
<div class='term in d4'><span class='muted'># check: is the Host header "localhost"?</span><br>Host: 127.0.0.1:3080 <span class='bad'>← set by the caller</span></div>
<div class='box bad in d8'><p class='mono' style='font-size:40px'>"... is not an auth layer"</p><p class='muted' style='font-size:30px;margin-top:10px'>— code comment</p></div></div>"""
+ src("Source: GitHub advisory GHSA-8m2g-8cgm-3vcp; The Hacker News"), chapter="How the escape worked")

beat("b06", """Now, the agent did not have to find this API. The harness gave the agent's shell the interface
address and the current session ID. And because the sandbox only blocked writes, the agent could still reach
localhost.""",
"<div class='stage'><div class='kicker warn in'>No searching needed</div>" + FLOW +
"<p class='in d8 muted'>The shell was handed the API address <i>and</i> the session ID.</p></div>" + src(SRC_THN))

beat("b07", """So one shell command, and the session flips to danger-full-access. Sandbox off. Approval prompts
off. And the harness recorded that change as if the user made it.""",
"""<div class='stage'><div class='kicker bad in'>One command later</div><div class='row'>
<div class='box bad pop d1'><h3>Sandbox</h3><p class='bad' style='font-size:64px;font-weight:800'>OFF</p></div>
<div class='box bad pop d3'><h3>Approval prompts</h3><p class='bad' style='font-size:64px;font-weight:800'>OFF</p></div>
<div class='box bad pop d5'><h3>Audit log</h3><p class='bad' style='font-size:46px;font-weight:800'>"by user"</p></div></div></div>"""
+ src("Source: The Hacker News; Forkast"))

beat("b08", """Researchers at OX Security tested it with two sessions on the same default settings. The normal
session was blocked from writing outside its workspace. The session that made the API call wrote straight into
the home directory, and no approval event appeared in the logs.""",
"""<div class='stage'><div class='kicker info in'>The OX Security test</div><div class='row'>
<div class='box good in d1'><h3>Session A · normal</h3><div class='term' style='margin-top:18px;font-size:30px'>write ~/file<br><span class='accent'>✗ blocked by sandbox</span></div></div>
<div class='box bad in d4'><h3>Session B · called the API</h3><div class='term' style='margin-top:18px;font-size:30px'>write /home/ubuntu/file<br><span class='bad'>✓ written · no approval logged</span></div></div></div></div>"""
+ src("Source: The Hacker News; Forkast"))

beat("b09", """To trigger it, an attacker needs the agent to read text they control. That is prompt injection,
nothing but instructions hidden in content the agent reads. No exploitation in the wild has been reported.""",
"""<div class='stage'><div class='kicker warn in'>The catch</div><h2 class='in d1'>Needs <span class='warn'>prompt injection</span></h2>
<p class='in d3 muted'>Attacker-controlled text that the agent reads.</p>
<div class='pill accent in d7' style='align-self:flex-start'>No exploitation in the wild reported</div></div>"""
+ src("Source: The Hacker News; Yahoo Tech"))

beat("b10", """The timeline is the uncomfortable part. On August 13, a community developer posted this exact escape
in the project's GitHub discussions. OX reported it on August 24. The fix shipped on GitHub on August 27, and on
npm on August 30. The CVE came out on September 8, rated 9.4 critical by VulnCheck.""",
"""<div class='stage'><div class='kicker in'>Timeline · 2026</div><div class='row' style='gap:24px'>
<div class='box in d1'><h3 class='warn'>Aug 13</h3><p style='font-size:34px'>Community dev posts the escape (Discussion #250)</p></div>
<div class='box in d3'><h3>Aug 24</h3><p style='font-size:34px'>OX reports to VulnCheck</p></div>
<div class='box in d5'><h3>Aug 27</h3><p style='font-size:34px'>Fix on GitHub</p></div>
<div class='box in d7'><h3>Aug 30</h3><p style='font-size:34px'>Fix on npm</p></div>
<div class='box bad in d9'><h3 class='bad'>Sep 8</h3><p style='font-size:34px'>CVE, 9.4 critical</p></div></div></div>"""
+ src("Source: GitHub discussions; npm registry; The Hacker News; NVD"), chapter="Timeline")

beat("b11", """And the release notes? One routine line about a launch token. No security notice. No CVE.""",
"""<div class='stage'><div class='kicker in'>Release notes · dsh v0.1.2-alpha.1</div>
<div class='box in d1'><p class='mono' style='font-size:40px'>• Require the one-time token in the launch URL</p></div>
<div class='in d5' style='display:flex;gap:28px'><div class='pill bad' style='font-size:44px;white-space:nowrap'>No security notice</div><div class='pill bad' style='font-size:44px;white-space:nowrap'>No CVE</div></div></div>"""
+ src("Source: GitHub release dsh-v0.1.2-alpha.1"))

beat("b12", """The fix is nothing but real authentication. A one-time token is printed at startup and swapped for a
signed cookie, and every call needs it. A forged Host header no longer works.""",
"""<div class='stage'><div class='kicker in'>The fix</div><h2 class='in d1'>Real authentication</h2>
<div class='row in d3' style='align-items:center'><div class='box'><p>One-time token at startup</p></div><p style='flex:0' class='accent'>→</p><div class='box'><p>Signed cookie</p></div><p style='flex:0' class='accent'>→</p><div class='box good'><p>Required on every call</p></div></div>
<p class='in d7 muted'>Forged Host header: <span class='accent'>rejected</span></p></div>"""
+ src("Source: fix commit 3e24087; The Hacker News"), chapter="The fix")

beat("b13", """But here is what did not change. Reads and network access are still not confined, and the agent's
shell still gets the interface address. The door is locked now. The agent can still reach it.""",
"""<div class='stage'><div class='kicker warn in'>What did NOT change</div><ul>
<li class='in d1'>Reads: <span class='warn'>not confined</span></li><li class='in d3'>Network: <span class='warn'>not confined</span></li>
<li class='in d5'>Agent shell still gets the API address</li></ul>
<h2 class='in d8' style='margin-top:20px'>The door is locked. <span class='warn'>The agent can still reach it.</span></h2></div>"""
+ src(SRC_THN))

beat("b14", """So what should you do? Update dsh to 0.1.2-alpha.2 or later. If you use a desktop app that bundles
it, check which version it ships. And if you tunneled or forwarded that port anywhere, treat your stored
conversations as possibly exposed.""",
"""<div class='stage'><div class='kicker in'>Do this</div><ul>
<li class='in d1'>Update to <span class='mono accent'>0.1.2-alpha.2</span> or later</li>
<li class='in d3'>Desktop wrapper? Check the bundled version</li>
<li class='in d5'>Ever tunneled port 3080? Treat transcripts as exposed</li></ul></div>"""
+ src("Source: The Hacker News; Neomanex"), chapter="What to do")

beat("b15", """My verdict. The bug is fixed, and the tool is still worth trying. But DeepSeek's own safety file
says it has not undergone a security audit and must not be treated as secure. Believe that. Run it in a throwaway
workspace, and never assume localhost means you.""",
"""<div class='stage'><div class='kicker in'>Verdict</div><h2 class='in d1'>Fixed. Worth trying. <span class='warn'>Not secure.</span></h2>
<div class='box in d4'><p class='mono' style='font-size:36px'>"It has not undergone a security audit and must not be treated as secure or production-ready."</p><p class='muted' style='font-size:28px;margin-top:10px'>— dsh SAFETY.md</p></div>
<p class='in d9'>Throwaway workspace. <span class='accent'>Localhost ≠ you.</span></p></div>"""
+ src("Source: github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md"), chapter="Verdict")

beat("b16", """The bigger lesson. A sandbox that only watches files is not a sandbox. If your agent can reach the
network, it can reach whatever controls it.""",
"""<div class='stage'><h1 class='in'>A sandbox that only watches files <span class='bad'>is not a sandbox.</span></h1></div>""")

beat("b17", """Next, I am testing DeepSeek Harness itself, live, with a free open model. If you want that,
subscribe. That's all from my side. Thank you everyone, have a good one.""",
"""<div class='stage'><div class='kicker in'>Next</div><h2 class='in d1'>DeepSeek Harness, tested live<br><span class='muted'>with a free open model</span></h2>
<div class='pill accent pop d5' style='align-self:flex-start'>Subscribe</div></div>""")


# Engagement pass (Priyesh, 2026-10-22): dry humour + "Pro tip" cards. Humour only comments on
# facts already in the video; tips are sourced or general security practice. No new claims.
REWRITE = {
"b02": """Your coding agent asks before it does anything risky. But in DeepSeek Harness, it could stop
asking, and the log said you approved it. That's like a security guard who can sign his own leave
approval, and then forges your signature on it. In this video, I'll show you exactly how that worked,
what the fix changed, and what it did not change.""",
"b05": """And that is the whole bug. The web UI is controlled by a local API. That API had no
authentication. It only checked the Host header, which the caller can simply set. And the code comment
literally says, this is not an auth layer. Well, at least the code was honest.""",
"b07": """So one shell command, and the session flips to danger-full-access. Sandbox off. Approval prompts
off. And the harness recorded that change as if the user made it. So congratulations, you just approved
something you never saw.""",
"b10": """The timeline is the uncomfortable part. On August 13, a community developer posted this exact escape
in the project's GitHub discussions. OX reported it on August 24. The fix shipped on GitHub on August 27,
and on npm on August 30. The CVE came out on September 8, rated 9.4 critical by VulnCheck. So, as usual,
the community was faster than the paperwork.""",
"b11": """And the release notes? One routine line about a launch token. No security notice. No CVE. If you
only read release notes, you would never know you had to update.""",
}
TIPS = {
"b06": ("t1", """Pro tip. Treat every localhost port on your machine as public to anything running on your machine.
That includes your agent. If a local tool exposes an API without a token, your agent can call it, and so can
anything your agent downloads.""",
"<div class='stage'><div class='kicker warn in'>Pro tip</div><h2 class='in d1'>Localhost is <span class='warn'>not</span> a trust boundary.</h2>"
"<ul><li class='in d4'>Every local process can reach it, <span class='warn'>including your agent</span></li>"
"<li class='in d6'>No token on a local API = an open door</li></ul></div>"),
"b09": ("t2", """Pro tip. Run coding agents inside a container or a virtual machine, with outbound network blocked
by default. Then open only what the task needs. Is it more setup? Yes. Is it less setup than explaining to
your team why the agent pushed your secrets? Also yes.""",
"<div class='stage'><div class='kicker warn in'>Pro tip</div><h2 class='in d1'>Box the agent, not just its files</h2>"
"<div class='term in d4'><span class='prompt'>$</span> docker run <span class='warn'>--network none</span> -v $PWD:/work my-agent-image</div>"
"<p class='in d7 muted'>Block network by default. Open only what the task needs.</p></div>"),
"b14": ("t3", """Pro tip. Before you install any agent tool, check whether the repo has a security policy, a way to
report bugs privately. According to The Hacker News, this repo had neither. That doesn't make a tool bad,
but it tells you how a bug like this will be handled.""",
"<div class='stage'><div class='kicker warn in'>Pro tip</div><h2 class='in d1'>Check for <span class='mono warn'>SECURITY.md</span> first</h2>"
"<ul><li class='in d4'>Is there a private way to report bugs?</li><li class='in d6'>Here: <span class='bad'>no security policy, no private channel</span></li></ul></div>"
"<div class='source'>Source: The Hacker News, Sep 9 2026</div>"),
}
for b in B:
    if b["id"] in REWRITE:
        b["say"] = " ".join(REWRITE[b["id"]].split())
out = []
for b in B:
    out.append(b)
    if b["id"] in TIPS:
        tid, say, html = TIPS[b["id"]]
        out.append({"id": tid, "say": " ".join(say.split()), "html": html, "chapter": None, "css": ""})
B[:] = out

# Pronunciation overrides: captions keep "say", the voice reads "tts".
SPOKEN = {"dsh": "D S H", "npm": "N P M", "0.1.2-alpha.2": "zero point one point two alpha two"}
for b in B:
    t = b["say"]
    for k, v in SPOKEN.items(): t = t.replace(k, v)
    if t != b["say"]: b["tts"] = t

json.dump({"title": "DeepSeek's Agent Could Turn Off Its Own Sandbox", "beats": B},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.json"), "w"), indent=1)
w = sum(len(b["say"].split()) for b in B); print(w, "words ->", round(w / 125, 1), "min at 125 wpm")
