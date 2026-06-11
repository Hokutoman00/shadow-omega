# Shadow-Omega Copilot certificate demo narration.
# Generates narration-copilot-certificate.wav in this directory.
# Uses Windows SAPI only; no browser, no screen capture, no desktop input.
param(
    [string]$OutFile = "$PSScriptRoot\narration-copilot-certificate.wav"
)

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

$voices = $synth.GetInstalledVoices() | Where-Object { $_.Enabled }
$zira = $voices | Where-Object { $_.VoiceInfo.Name -like "*Zira*" } | Select-Object -First 1
$david = $voices | Where-Object { $_.VoiceInfo.Name -like "*David*" } | Select-Object -First 1
if ($zira) {
    $synth.SelectVoice($zira.VoiceInfo.Name)
    Write-Host "Using voice: $($zira.VoiceInfo.Name)"
} elseif ($david) {
    $synth.SelectVoice($david.VoiceInfo.Name)
    Write-Host "Using voice: $($david.VoiceInfo.Name)"
} else {
    Write-Host "Using default voice: $($voices[0].VoiceInfo.Name)"
}

$synth.Rate = 2
$synth.Volume = 100
$synth.SetOutputToWaveFile($OutFile)

$ssml = @'
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<prosody rate="1.10" volume="loud">

<break time="500ms"/>
Shadow Omega, Copilot Convergence Certificate.
<break time="450ms"/>
The first demo explained the multiverse. This final demo proves the post-stage loop.

<break time="800ms"/>
The submission now exposes a Copilot-facing MCP server.
Copilot can ask for an audit, request a convergence certificate, and run a closed-loop mitigation demo.

<break time="750ms"/>
The target is concrete: a transfer function where balance checks, debit, credit, and persistence are split across separate operations.
That creates a non-atomic value transfer risk that can survive a normal single-path code review.

<break time="850ms"/>
Shadow Omega sends the code into five independent adversarial universes.
They do not share information.
Three of the five converge on the same finding: non atomic value transfer.
The certificate records the vote, the attack surface, the strategy fingerprint, and confidence: zero point nine six.

<break time="850ms"/>
The important part is what happens next.
The MCP tool runs a guarded patch plan: transaction boundary, locked reads, amount validation, and invariant checks.
Then it re-audits the patched shape.
The original pattern is no longer converged, so the closed-loop result is mitigated.

<break time="850ms"/>
The discovery also leaves a reusable artifact behind: an ESLint rule skeleton for the Fossil Record.
That means the evolved vulnerability is not just described in a video.
It becomes something a developer workflow can call again.

<break time="800ms"/>
For judges, this strengthens the submission in four ways:
novelty, because consensus becomes an audit primitive;
technical proof, because the verifier checks six MCP tools;
usefulness, because Copilot can request the certificate;
and demo clarity, because the video shows fixture, votes, patch, and re-audit in one path.

<break time="800ms"/>
The repository is honest about the current boundary:
the non-interactive Copilot CLI preview did not expose custom workspace MCP tools.
So the submitted proof includes explicit setup instructions, a usage log, and a verifier that exercises the MCP server directly.

<break time="650ms"/>
Run the verifier, inspect the fixture, and call generate convergence certificate or run closed loop demo.
Shadow Omega is now not only an idea.
It is a reproducible Copilot-ready audit workflow.

<break time="900ms"/>
</prosody>
</speak>
'@

try {
    $synth.SpeakSsml($ssml)
    Write-Host "Narration written to: $OutFile"
} finally {
    $synth.Dispose()
}
