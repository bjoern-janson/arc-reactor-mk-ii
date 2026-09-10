# ARC-MKII-V2 G3 Executable Implementation Record

**Status:** `V2 G3 EXECUTABLE IMPLEMENTATION: PASS / IMPLEMENTATION_FROZEN / NO_V2_SCIENTIFIC_RESULT`

G3_IMPLEMENTATION_FREEZE_ID_V2: cd4890e6bba947ef9399043b10d3747680609800
G3_DESIGN_FREEZE_ID: b6d520eafd81b367c81c145d05c4702dac94b74c
G2_RECORD_ID: 5689645287c41a71e109f1b022529e8b98f2006d
G2_PROTOCOL_MANIFEST_SHA256: 419b7be408a5a37ab6a7ee304ac58646683a6fc4771b503e0b0f475002b4d075
workflow run: 34471835729

## Executability custody

```text
V2 TRAIN rows: 817105
(2,0): size=61440 offset=26027 row_ids_sha256=0bcc9fe377e1f0aa573865d7305022cefd622d40ee452f1f7d912ad5a0ed3654
(2,1): size=60805 offset=11302 row_ids_sha256=71132d31d6cefcf5c2d236275a6cec2d9bc1573cad785e8dc4bcb521afdc595b
(3,0): size=245760 offset=167833 row_ids_sha256=71eac513f895ebe9a39a8300acc54dc00ed62d8614936e0c99b4e21d021178e5
(3,1): size=243220 offset=12092 row_ids_sha256=5cddc338d1ecd2d5bd17f3a4eaa676104ffa4e7d3042e416506ee1f6309e0925
(3,2): size=205880 offset=92488 row_ids_sha256=e498c5667a0af60001c1acdb23618847512ad606e147f0e9b403768c956cc488
canonical_task_identity: family_id
frozen scientific primitives: BYTE-UNCHANGED FROM G2
G4 trigger: run/v2-g4-official ONLY
G4 lock before first fit: VERIFIED BY STATIC TOPOLOGY
primary fossil before root autopsy: VERIFIED BY STATIC TOPOLOGY
```

## Result-isolation boundary

```text
NO LEARN FIT
NO SCRAMBLED FIT
NO EVAL EXECUTION
NO ROOT-AUTOPSY VALUES
NO IGNITION
NO V2 SCIENTIFIC RESULT
```

G3 verified the exact 817,105-row TRAIN identity bridge against all five G2-frozen SCRAMBLED strata and froze result-capable execution machinery without running it on the frozen V2 scientific evaluation.

## Authorization boundary

```text
G4 RESULT-BEARING EXECUTION AUTHORIZED ONLY
```

G4 is not triggered by this fossil. A future explicit `run/v2-g4-official` ref must be created separately and must point exactly to the frozen G3 executable record.
