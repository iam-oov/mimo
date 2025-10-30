#!/usr/bin/env python3
"""
Quick test script for multi-agent analysis system.
Tests the core functionality without requiring the full server.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    try:
        from multi_agent_analysis import (
            Personality,
            Profession,
            AgentFactory,
            MultiAgentAnalysisService,
            build_taxpayer_context
        )
        from tabla_isr_constants import get_tabla_isr
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_enums():
    """Test that enums are properly configured."""
    print("\n🧪 Testing enums...")
    try:
        from multi_agent_analysis import Personality, Profession
        
        print(f"  Personalities available: {len(Personality)}")
        for p in Personality:
            print(f"    - {p.value}")
        
        print(f"  Professions available: {len(Profession)}")
        for p in Profession:
            print(f"    - {p.value}")
        
        print("✅ Enums configured correctly")
        return True
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        return False


def test_agent_factory():
    """Test agent factory creation."""
    print("\n🧪 Testing agent factory...")
    try:
        from multi_agent_analysis import AgentFactory
        
        # Test moderator creation
        moderator = AgentFactory.create_moderator()
        print(f"  ✅ Moderator created: {moderator.name}")
        
        # Test expert creation (requires AI API key)
        if not os.getenv('DEEPSEEK_API_KEY') and not os.getenv('GEMINI_API_KEY'):
            print("  ⚠️  Skipping expert creation (no AI API key found)")
            print("     Set DEEPSEEK_API_KEY or GEMINI_API_KEY to test fully")
            return True
        
        experts = AgentFactory.create_random_experts(count=3)
        print(f"  ✅ Created {len(experts)} experts:")
        for expert in experts:
            print(f"     - {expert.profile.name}: {expert.profile.profession_traits.title}")
            print(f"       Personality: {expert.profile.personality_traits.name}")
        
        print("✅ Agent factory working correctly")
        return True
    except Exception as e:
        print(f"❌ Agent factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_taxpayer_context():
    """Test taxpayer context building."""
    print("\n🧪 Testing taxpayer context builder...")
    try:
        from multi_agent_analysis import build_taxpayer_context
        from tabla_isr_constants import get_tabla_isr
        
        # Mock calculation result
        class MockResult:
            gross_annual_income = 151200.00
            total_taxable_income = 155137.50
            authorized_deductions = 71000.00
            personal_deductions = 58000.00
            ppr_deductions = 8000.00
            education_deductions = 5000.00
            taxable_base = 84137.50
            determined_tax = 12500.25
            withheld_tax = 15000.00
            balance_in_favor = 2499.75
            balance_to_pay = 0.00
        
        user_data = {
            "ingresos": {
                "ingreso_bruto_mensual_ordinario": 12600.00,
                "dias_aguinaldo": 15,
                "dias_vacaciones_anuales": 12,
                "porcentaje_prima_vacacional": 0.25,
            },
            "contribuyente": {
                "nombre_o_referencia": "Test User",
            },
        }
        
        context = build_taxpayer_context(MockResult(), user_data, 2025)
        
        print(f"  ✅ Context generated ({len(context)} characters)")
        print("\n  Preview:")
        print("  " + "-" * 60)
        print("  " + context[:300].replace("\n", "\n  "))
        print("  " + "..." if len(context) > 300 else "")
        print("  " + "-" * 60)
        
        print("✅ Taxpayer context builder working")
        return True
    except Exception as e:
        print(f"❌ Context builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_keys():
    """Test that required API keys are present."""
    print("\n🧪 Testing API configuration...")
    
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if deepseek_key:
        print(f"  ✅ DEEPSEEK_API_KEY: Configured (***{deepseek_key[-8:]})")
    else:
        print("  ⚠️  DEEPSEEK_API_KEY: Not set")
    
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY: Configured (***{gemini_key[-8:]})")
    else:
        print("  ⚠️  GEMINI_API_KEY: Not set")
    
    if not deepseek_key and not gemini_key:
        print("\n  ❌ No AI provider configured!")
        print("     Set at least one of: DEEPSEEK_API_KEY or GEMINI_API_KEY")
        return False
    
    print("✅ At least one AI provider configured")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("🚀 Multi-Agent Analysis System - Quick Test")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Enums", test_enums),
        ("API Keys", test_api_keys),
        ("Agent Factory", test_agent_factory),
        ("Taxpayer Context", test_taxpayer_context),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
