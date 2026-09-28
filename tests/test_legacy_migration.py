"""Historical Copilot migration fixtures for the P3 lifecycle engine.

The packed blobs are byte-for-byte files from Copilot RPI 56efd8e1 (2026-09-28).
Their SHA-256 values are independent identity oracles, not ownership inferred
from sync metadata. Every test uses disposable source and target Git repos.
"""

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "templates/scripts/rpi-distribution.py"
HISTORICAL_COMMIT = "56efd8e1fe242054123761f92a74a0ae86d13eca"

# Each tuple is (historical source path, SHA-256, zlib/base85 payload).
HISTORICAL = {
    'status': (
        'templates/prompts/status.prompt.md',
        'd4d8dd8071249777075e09ca85777af309baf78e3879976d17b456bfab731b91',
        'c-'
        'nPR%Wm5+5WMp%7C{fT5y?p0Tm(Zv>!gK?#_q#Fdo)9>Ek+bc@ZmJKenh{pU(zKdBj_PFk~=$`ncbo&SZ^AvfFDr@)}R+'
        'o+8~Xt;A@nk1MAEqiU2<F5Iu+%>GALHKX6khsS%8m)X7r|D~Rr%=oAEru7cUD<+6*jS#FT}WIBY<N}pJJ8|Vo*9Jmj2;'
        '^h`RdQU_!=~1*?OTmeX`)*n?_PU%BwlUZkh)WnPr2kJ9aNQ8xSmO8=HT{nS5T@^`;B(bFdeR}4fR0fGKS(2#<>|LbX!l'
        '$(c2&auC<8n=u0;z);al@mi0B*<?6c4DGD6t(*rCjk;6`JPtym0TMdo3V<;dXKVg!%&GQAslqaIKJ8%XIK(ZfU@$iefJ'
        'y-kfRI5MatQ5MCh@Xh2^xl_6;NsMqsr$<j&rTkP(Gq@ZiTx#AUT-'
        'WmkPjelWI?E17zpU10r4!#t3#5ibM9oiJD*m8w%5F+n<()Ygm!!gOd%K-~SpU4g0~xT-Nx%Dex7mF!`-TPw#-'
        'h$s_l$iRC&Ot_=Z$+A#(uvK_$#pY*<A(8!Dh`qr&Ncu=(VS<qW!L6vTV6;>nZzTTqpGrf<xN<rBKK<%wYousnCz<HZ@z'
        'VsX96&Wf$6zl(V;snr)NR>>{z4NJ<BoPF0e}*sX!hc9&vuA^SJ9We%Q5K?$EC>2zpm#^)ekw)G#e06<L',
    ),
    'research_chatmode': (
        'templates/github/chatmodes/rpi-research.chatmode.md',
        '35a2cee9500c33d07ddf89743f4e242287cbd88089f5a81a0fbf5ecaf5947a91',
        'c-'
        'l==%Wm6147}?r2>X!Mh*O}w`IcAP072Z^4%)&9U|OQ=MfRcWBd%}#h<;(eq_dLc_@W1?<qU^IjmP7{vXKeRzTMGGg0L^'
        'QMJ1v1s)@?k2@U%2*jc?N<0_$lfBsVU(OLrSwj4=*s}RFES$P#tA#FB-cPh7R@iZu+b2?0DIVe$J%|Qm|G^mws?;91jX'
        '+4w14W5cINd0n&*b6C3qtPk17JoFlD2m~bF0ba(`^UvCT~8n8i`nJf!(u}HQKrh3$%u{Y6<eGbjcyK{JIc2|@8*m71wE'
        'Wn?o#uw)5rT8y1Km>jf!HiRe_AK4U?i6)5DaMX}o)tT)jUCu|k(bYOTePs*qN-Dmf>+oOdo#$ti%KWxWrm{4QB7Awa@L'
        't5QX%%;8z8_uY{!7`-IcD(>-'
        'Ox|a3_Eb+DThHWXx;p%%9LCWOwksW)h?B)>mQga!dM+DDZxr$HN57rVR^xy`4aJkLH%VI-UPcFqKMQR~qQOu)HWlULZt'
        '*KVF%0OTb^?g6FehkoVwOSeW&z0NRVtAY>T(NMCDxX@Mc`_!qxBNK%geGhhbQOBLW!mk8_84>RlC8Q^Hxe0Us_6591cF'
        '0aUOUq`iy|K`z3@}9ym_-'
        'W?ch4f7My5hB`YJo1?x&)XWeJVV6j{<#!9Znms(yKqtAx}ZM;hjpw}1=N7*>P?<!0ivGhIl=2-'
        'sdiI*<v%AQ4Z1*uI&&np$TlBI0r-'
        '0?n;%LQKg0#8}Lw(u+gH(T)*&IPJwWymDBSJ_ghD!YGm>}>VcS{`xh_8qJtGzi<wB(GpgiLe?6Yq!DOA!wym=+--'
        'fsKc%(qcnTcSnkA|T=uT+Oq;!tdxTdSWkLHK=;*M@-4T56@zBX|)-'
        'AX{U2SYdb^NtZwrapPAqrOjnc;R29nNhu)Wfo@1(<T`5I~t$QR@g6wZ{$ol1KGs)OEX1okMb8ke=}i!-'
        '^tvVC8%zzW5J0{>bD',
    ),
    'tests_instruction': (
        'templates/github/instructions/tests.instructions.md.template',
        '31bef67c611b583765ade88d43313686ba786e802bce9d1d6b569c987681c734',
        'c-m!D%Z}VO5WMRv8ur1vgVFdApEjrUIx%wa1G{7ADvD}J+@(mFY|e}j1jt9^3-'
        'cu|QnNOU00WGuW_MRrSF5h;O3kxf_Wp{VY&Op~JK-q1za(xYp0@W9zti7Osu~xc(jGDT-B_j@?+)z5co(bcDI#y*(x>3'
        'XYj3OS+FH`SW74B?14rt;wf;!A+|};_v#W2pS6Y0ys$TABvq509q5uB*m;MY!m=yKOSmOqg((;enyZx40?tNeqpY)hxW'
        '|}QefT1#w(y@A#%atBK6_k-_GR{nCT9JvTNj<EA(qmRJR==!ZR&3`2H<p#7G}Cd+%paKNM_`eL+-'
        'X%H7rB#=w4}gQRnzCl)N~wmFfBLKTCX2+hEFqh)GpK~rwei)Xkr<CN6B>@N^KOlwnw!@GEUpn@fD32)dHY0Ziz!cmR6A'
        '?4&A`(GqT>KfqHX->hC|_?J0^1LPsMbR1FNkG3K6yw2Vsdat^*r8W~xQHVuW)d%y+J%p^Y&pM--`mO7ppFr7BYxNs~-'
        'A0D>UDN!vjY|$M$#U%<)m&pFW2XLBljWP!GLi{JDS*lg^AF5>6tQSh@EjbUY>PWu5XDwtg*Pv{s{3&pcV&8!+&@A66+O'
        'Ew@&uOKENiuvidnnObE^I%j=}fi^avj^e;)tV9wu4TpBZcG4+Vn;j*TpMpj9femjIrbH>ld$cc^D?5Z-'
        '(4^P<?jU<bfW%>FA(_#N^b(kI7lU2w#Q((00LPGO;8pt$Bv7Kv~nfY#qR`N?@SXfX0!-'
        '1J3`mTH$paf#bZVHGOnU)(^mL!Q>pF`8)`^n35HPrJ{yUU?~k;Wo;w{xq5?S)0dlBM2}<3qdFKLF3&Su=Zi{@8ez#qLv'
        '2zAEOh2U7tK!mZ(ozL%{rWXe#85aWL%odAHH7!o}Dhs%<(xSi)zT0&*I#tM+;*?*K0?WO&t7jUCJ*UzE6to_-'
        'o3p&11ez_+E^h7c!RDVnB33-C|Z$nH9`s*%FomtAX9xRX3wD4l~PON;drp8#=*XR;8)F0k1vUv;',
    ),
    'process_errors': (
        '.github/prompts/process-errors.prompt.md',
        '5bb8400cfcd58fc1ca843bc45af3835c22c4cabe1a4c3b31ee8e1e6ad5419426',
        'c-oCr%Wl*#6y5tPuG$4{)TH7K*;OswP)gOQgxHNqZYE|DJJ`-'
        'VHi(bl3;7a`orKP)1+k0#IInx+G)+ZoO3q0xSbI^jE3E3gGCHS&8*2)7j@Vjb2|LW%)y6xjtZB*D{MeRhO11|g1@s3%H'
        '{=!DoRY*Dt=T6D{rd5flwO%714B9LfYx~|k)&BXL=L<VkqL1~lZ<zfYj)2i#Anl!v>Xt^5v3QTc|DjJwRO^awtCdOtJK'
        '%hM-#ncOSN?5<ciC{c}O$Q9SELgbfugp*)*hD;8LX;c0ud>`{@O{r8nJa<Vz!;JDt-JXajCxbfp%(<?^pN9gAlfU1E!6'
        'Q4b6!#2eWv&7>gDkSYPLs_jnRqbKn^qg$3G%_oz4O0u?`2Y{mHVhKKwY~Uq?ghN)b6E7YBeCt)QOf6SzSr;5Js>x4pZ3'
        'x!(O)%G^FfVu1Cke90cn6I~ZmBvd`>s)i^z4pvK}0E?m1Pk156MWTG3y{RI^M{_2MH~vWvT}rB5VLolA$1n*Rf!;+E`B'
        ')Q=wN(cgi=MB-8oX7Ns+7PV1=$Lu~*N3*i_6jc0F-'
        '@pLY+9*%E^+San`FwN=Axj{ORde)(h$Rm%KmD)@PJ_VlZk9WcTg~^d%+Zs)4Yv4wXw+7B3CP_wf+Mo({KeES$v{t^3jG'
        '8y&h;-k6VJlu`(AKtUXmL?Xy+DKG`4&G7T<0{0PCNo2-3!sh5O-dMxp<w?P4DU;$Z~5ui#Hi!ZrC%OU0qGTB03-'
        '2{2y<HcpF;S1*SNPHU2~>0fN-!{Zi;t7Z%-'
        '4tKz?U3$yqN6`1XpZhCC09RZk}Y%E&8#ROJJusosC=qEnf4=F9A(h==Fb2s&jP!6`L7$LO@PQPN{sq45<l`81ZKwP|i8'
        'GC$R*s;U0(9L$l!5iVQk6T-6<9vt9W1?e*vcksBD>q(_1&bMmN%c)hU*Hn8-Xb>E!4`|(ScMKE',
    ),
}


def old_bytes(name):
    source, expected_hash, *pieces = HISTORICAL[name]
    data = zlib.decompress(base64.b85decode("".join(pieces)))
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise AssertionError(f"historical fixture changed: {source}")
    return data


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def invoke(*args):
    return subprocess.run(
        [sys.executable, str(ENGINE), *(str(arg) for arg in args)],
        text=True, capture_output=True, check=False,
    )


def git(*args):
    return subprocess.run(["git", *map(str, args)], text=True, capture_output=True, check=True).stdout.strip()


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.package = self.base / "package"
        self.source = self.base / "legacy-source"
        self.target = self.base / "target"
        self.source.mkdir()
        self.target.mkdir()
        git("init", "-q", self.source)
        git("init", "-q", self.target)
        for repo in (self.source, self.target):
            git("-C", repo, "config", "user.name", "Fixture")
            git("-C", repo, "config", "user.email", "fixture@example.invalid")
        for name in HISTORICAL:
            source_path = HISTORICAL[name][0]
            if name == "process_errors":
                # The maintenance prompt was self-applied, never a templates/prompts file.
                source_path = ".github/prompts/process-errors.prompt.md"
            write(self.source / source_path, old_bytes(name))
        git("-C", self.source, "add", ".")
        git("-C", self.source, "commit", "-qm", "fixture historical Copilot bytes")
        self.legacy_commit = git("-C", self.source, "rev-parse", "HEAD")
        rendered = invoke("render", "--source", ROOT, "--profile", "cli", "--target", self.package)
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)

    def plan(self, name="plan", provenance=True):
        output = self.base / f"{name}.json"
        args = ["plan", "--package", self.package, "--target", self.target, "--profile", "cli", "--output", output]
        if provenance:
            args.extend(("--legacy-source", self.source, "--legacy-base", self.legacy_commit))
        result = invoke(*args)
        payload = json.loads(output.read_text()) if output.is_file() else None
        return result, payload, output

    def apply(self, plan_path):
        return invoke("apply", "--plan", plan_path)

    def assert_path_reported(self, payload, path):
        report = json.dumps(payload, sort_keys=True)
        self.assertIn(path, report)

    def test_exact_historical_prompt_and_chatmode_retire_after_reviewed_plan(self):
        status_path = self.target / ".github/prompts/status.prompt.md"
        chatmode_path = self.target / ".github/chatmodes/rpi-research.chatmode.md"
        custom_path = self.target / ".github/prompts/team.prompt.md"
        write(status_path, old_bytes("status"))
        write(chatmode_path, old_bytes("research_chatmode"))
        write(custom_path, b"---\nagent: agent\ndescription: Team.\n---\n\n# Team\n")
        result, preview, plan_path = self.plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIsNotNone(preview)
        self.assertFalse(preview["conflicts"], preview)
        self.assert_path_reported(preview["legacy"], ".github/prompts/status.prompt.md")
        self.assert_path_reported(preview["legacy"], ".github/chatmodes/rpi-research.chatmode.md")
        applied = self.apply(plan_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertFalse(status_path.exists())
        self.assertFalse(chatmode_path.exists())
        self.assertTrue((self.target / ".github/skills/rpi-status/SKILL.md").is_file())
        self.assertTrue((self.target / ".github/agents/rpi-research.agent.md").is_file())
        self.assertEqual(custom_path.read_bytes(), b"---\nagent: agent\ndescription: Team.\n---\n\n# Team\n")

    def test_false_sync_metadata_does_not_prove_modified_prompt_ownership(self):
        status_path = self.target / ".github/prompts/status.prompt.md"
        modified = old_bytes("status") + b"\n# Owner note\n"
        write(status_path, modified)
        sync_path = self.target / ".github/copilot-rpi-sync.json"
        sync = json.dumps({"lastSyncCommit": self.legacy_commit, "blueprintVersion": "1.18.0"}, indent=2).encode()
        write(sync_path, sync)
        result, preview, plan_path = self.plan()
        self.assertIn(result.returncode, (0, 2), result.stdout + result.stderr)
        self.assertIsNotNone(preview)
        self.assert_path_reported(preview["legacy"], ".github/prompts/status.prompt.md")
        self.assertFalse(any(action.get("destination") == ".github/prompts/status.prompt.md"
                             and action.get("action") == "remove" for action in preview["actions"]))
        self.assertEqual(status_path.read_bytes(), modified)
        self.assertEqual(sync_path.read_bytes(), sync)
        if result.returncode == 0:
            applied = self.apply(plan_path)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(status_path.read_bytes(), modified)
        else:
            refused = self.apply(plan_path)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(status_path.read_bytes(), modified)
        write(status_path, old_bytes("status"))
        repaired, ready, repaired_path = self.plan("replanned")
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertFalse(ready["conflicts"], ready)
        applied = self.apply(repaired_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertFalse(status_path.exists())
        self.assertEqual(sync_path.read_bytes(), sync)

    def test_sync_claim_alone_does_not_retire_even_exact_historical_bytes(self):
        status_path = self.target / ".github/prompts/status.prompt.md"
        original = old_bytes("status")
        write(status_path, original)
        sync_path = self.target / ".github/copilot-rpi-sync.json"
        sync = json.dumps({"lastSyncCommit": HISTORICAL_COMMIT, "blueprintVersion": "1.18.0"}).encode()
        write(sync_path, sync)
        unproven, preview, plan_path = self.plan("unproven", provenance=False)
        self.assertIn(unproven.returncode, (0, 2), unproven.stdout + unproven.stderr)
        self.assertIsNotNone(preview)
        self.assert_path_reported(preview["legacy"], ".github/prompts/status.prompt.md")
        self.assertFalse(any(action.get("destination") == ".github/prompts/status.prompt.md"
                             and action.get("action") == "remove" for action in preview["actions"]))
        self.assertEqual(status_path.read_bytes(), original)
        self.assertEqual(sync_path.read_bytes(), sync)
        if unproven.returncode == 0:
            applied = self.apply(plan_path)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(status_path.read_bytes(), original)
        else:
            refused = self.apply(plan_path)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(status_path.read_bytes(), original)
        reviewed, ready, reviewed_path = self.plan("reviewed", provenance=True)
        self.assertEqual(reviewed.returncode, 0, reviewed.stdout + reviewed.stderr)
        applied = self.apply(reviewed_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertFalse(status_path.exists())
        self.assertEqual(sync_path.read_bytes(), sync)

    def test_renamed_chatmode_is_retained_even_with_historical_bytes(self):
        renamed = self.target / ".github/chatmodes/research-renamed.chatmode.md"
        write(renamed, old_bytes("research_chatmode"))
        result, preview, plan_path = self.plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_path_reported(preview, ".github/chatmodes/research-renamed.chatmode.md")
        applied = self.apply(plan_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertEqual(renamed.read_bytes(), old_bytes("research_chatmode"))

    def test_custom_instruction_glob_is_preserved_and_recoverable(self):
        owned_path = self.target / ".github/instructions/tests.instructions.md"
        original = old_bytes("tests_instruction")
        self.assertIn(b"applyTo:", original)
        old_glob_line = next(line for line in original.splitlines(keepends=True) if line.startswith(b"applyTo:"))
        customized = original.replace(old_glob_line, b'applyTo: "**/owner-tests/**"\n', 1)
        write(owned_path, customized)
        result, preview, plan_path = self.plan()
        if result.returncode == 0:
            applied = self.apply(plan_path)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertIn(b"owner-tests", owned_path.read_bytes())
        else:
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assert_path_reported(preview, ".github/instructions/tests.instructions.md")
            self.assertEqual(owned_path.read_bytes(), customized)
            custom_path = self.target / ".github/instructions/owner-tests.instructions.md"
            owned_path.rename(custom_path)
            repaired, ready, repaired_path = self.plan("replanned")
            self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
            applied = self.apply(repaired_path)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(custom_path.read_bytes(), customized)
            self.assertTrue(owned_path.is_file())

    def test_self_applied_process_errors_retires_only_exact_old_prompt(self):
        old_path = self.target / ".github/prompts/process-errors.prompt.md"
        modified = old_bytes("process_errors") + b"\n# Owner note\n"
        write(old_path, modified)
        refused, unsafe_preview, unsafe_path = self.plan("modified-process-errors")
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assert_path_reported(unsafe_preview["legacy"], ".github/prompts/process-errors.prompt.md")
        self.assertFalse(any(action.get("destination") == ".github/prompts/process-errors.prompt.md"
                             and action.get("action") == "remove" for action in unsafe_preview["actions"]))
        self.assertIn("plan --package", refused.stdout + refused.stderr)
        self.assertEqual(old_path.read_bytes(), modified)
        unsafe_apply = self.apply(unsafe_path)
        self.assertNotEqual(unsafe_apply.returncode, 0)
        self.assertEqual(old_path.read_bytes(), modified)
        write(old_path, old_bytes("process_errors"))
        result, preview, plan_path = self.plan("reviewed-process-errors")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_path_reported(preview["legacy"], ".github/prompts/process-errors.prompt.md")
        applied = self.apply(plan_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertFalse(old_path.exists())
        self.assertTrue((self.target / ".github/skills/process-errors/SKILL.md").is_file())

    def test_cc_rpi_state_coexists_with_copilot_namespace(self):
        cc_manifest = self.target / ".rpi/manifest.json"
        cc_baseline = self.target / ".rpi/baselines/old-owner"
        write(cc_manifest, b'{"owner":"cc-rpi","schema_version":2}\n')
        write(cc_baseline, b"cc-rpi-owned\n")
        original = {cc_manifest: cc_manifest.read_bytes(), cc_baseline: cc_baseline.read_bytes()}
        result, preview, plan_path = self.plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(preview["conflicts"], preview)
        applied = self.apply(plan_path)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        for path, data in original.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertTrue((self.target / ".rpi/copilot/manifest.json").is_file())
        self.assertFalse((self.target / ".rpi/local/copilot").is_symlink())
        detach_plan = self.base / "detach-copilot.json"
        detached = invoke("detach", "--package", self.package, "--target", self.target,
                          "--profile", "cli", "--output", detach_plan)
        self.assertEqual(detached.returncode, 0, detached.stdout + detached.stderr)
        removed = self.apply(detach_plan)
        self.assertEqual(removed.returncode, 0, removed.stdout + removed.stderr)
        self.assertFalse((self.target / ".rpi/copilot/manifest.json").exists())
        for path, data in original.items():
            self.assertEqual(path.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
