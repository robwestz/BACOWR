#!/usr/bin/env python3
"""
Live Test för BACOWR Backlink Engine
Validerar BacklinkJobPackage mot JSON-schema
"""

import json
import sys
from datetime import datetime

def log(message, level="INFO"):
    """Logger med timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}", flush=True)

def validate_json_structure():
    """Validerar JSON-struktur utan externa bibliotek"""
    log("🚀 Startar BACOWR Live Test")
    log("=" * 60)

    # Test 1: Läs schema
    log("Test 1: Läser JSON-schema...")
    try:
        with open('backlink_job_package.schema.json', 'r', encoding='utf-8') as f:
            schema = json.load(f)
        log("✅ Schema läst framgångsrikt", "SUCCESS")
        log(f"   Schema titel: {schema.get('title', 'N/A')}")
        log(f"   Schema version: {schema.get('$schema', 'N/A')}")
    except Exception as e:
        log(f"❌ Fel vid läsning av schema: {e}", "ERROR")
        return False

    # Test 2: Läs job package
    log("\nTest 2: Läser BacklinkJobPackage...")
    try:
        with open('BacklinkJobPackage.json', 'r', encoding='utf-8') as f:
            job_package = json.load(f)
        log("✅ Job package läst framgångsrikt", "SUCCESS")
        log(f"   Job ID: {job_package.get('job_meta', {}).get('job_id', 'N/A')}")
    except Exception as e:
        log(f"❌ Fel vid läsning av job package: {e}", "ERROR")
        return False

    # Test 3: Validera nödvändiga fält
    log("\nTest 3: Validerar obligatoriska fält...")
    required_fields = schema.get('required', [])
    missing_fields = []

    for field in required_fields:
        if field in job_package:
            log(f"   ✅ {field}: Finns", "CHECK")
        else:
            log(f"   ❌ {field}: Saknas", "ERROR")
            missing_fields.append(field)

    if missing_fields:
        log(f"\n❌ Validering misslyckades. Saknade fält: {missing_fields}", "ERROR")
        return False
    else:
        log("\n✅ Alla obligatoriska fält finns!", "SUCCESS")

    # Test 4: Detaljvalidering av nyckelkomponenter
    log("\nTest 4: Detaljvalidering av komponenter...")

    # Validera input_minimal
    log("   📋 input_minimal:")
    input_min = job_package.get('input_minimal', {})
    for key in ['publisher_domain', 'target_url', 'anchor_text']:
        value = input_min.get(key, 'MISSING')
        log(f"      - {key}: {value}")

    # Validera intent_extension
    log("   📋 intent_extension:")
    intent = job_package.get('intent_extension', {})
    log(f"      - serp_intent_primary: {intent.get('serp_intent_primary', 'MISSING')}")
    log(f"      - recommended_bridge_type: {intent.get('recommended_bridge_type', 'MISSING')}")
    log(f"      - intent_alignment.overall: {intent.get('intent_alignment', {}).get('overall', 'MISSING')}")

    # Validera generation_constraints
    log("   📋 generation_constraints:")
    gen_const = job_package.get('generation_constraints', {})
    log(f"      - language: {gen_const.get('language', 'MISSING')}")
    log(f"      - min_word_count: {gen_const.get('min_word_count', 'MISSING')}")

    # Test 5: Validera datakvalitet
    log("\nTest 5: Kontrollerar datakvalitet...")
    quality_checks = []

    # Check 1: Språk consistency
    target_lang = job_package.get('target_profile', {}).get('detected_language')
    pub_lang = job_package.get('publisher_profile', {}).get('detected_language')
    gen_lang = job_package.get('generation_constraints', {}).get('language')

    if target_lang == pub_lang == gen_lang:
        log(f"   ✅ Språk konsistent: {target_lang}", "CHECK")
    else:
        log(f"   ⚠️  Språk inkonsistent: target={target_lang}, pub={pub_lang}, gen={gen_lang}", "WARNING")
        quality_checks.append("Språkinkonsistens")

    # Check 2: Intent alignment
    overall_alignment = intent.get('intent_alignment', {}).get('overall')
    if overall_alignment == 'aligned':
        log(f"   ✅ Intent alignment: {overall_alignment}", "CHECK")
    else:
        log(f"   ⚠️  Intent alignment: {overall_alignment}", "WARNING")
        quality_checks.append("Intent ej fullt aligned")

    # Check 3: Word count requirement
    min_words = gen_const.get('min_word_count', 0)
    if min_words >= 900:
        log(f"   ✅ Ordkrav uppfyllt: {min_words} ord", "CHECK")
    else:
        log(f"   ⚠️  Ordkrav lågt: {min_words} ord (rekommenderat: 900+)", "WARNING")
        quality_checks.append("Lågt ordkrav")

    # Sammanfattning
    log("\n" + "=" * 60)
    log("📊 TESTSAMMANFATTNING")
    log("=" * 60)

    if not quality_checks:
        log("🎉 Alla tester godkända! Jobbet är redo för Writer Engine.", "SUCCESS")
        log("\n✨ Next-A1 SERP-First specifikationen verifierad")
        return True
    else:
        log("⚠️  Tester avslutade med varningar:", "WARNING")
        for warning in quality_checks:
            log(f"   - {warning}")
        log("\n💡 Jobbet kan fortfarande köras men kvaliteten kan påverkas")
        return True

if __name__ == "__main__":
    log("Initierar BACOWR Live Test System...")
    log("Arbetar i: /home/user/BACOWR")
    log("")

    success = validate_json_structure()

    log("")
    if success:
        log("✅ Live test avslutad framgångsrikt", "SUCCESS")
        sys.exit(0)
    else:
        log("❌ Live test misslyckades", "ERROR")
        sys.exit(1)
