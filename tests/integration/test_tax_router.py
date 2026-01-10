"""
Integration tests for the tax calculation API router.
Tests the full request/response cycle through FastAPI.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.tax_calculation.infrastructure.api.tax_router import router


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with the tax router"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client"""
    return TestClient(app)


class TestCalculateEndpoint:
    """Tests for POST /api/calculate endpoint"""

    def test_basic_calculation_success(self, client: TestClient):
        """Basic tax calculation returns 200 with valid data"""
        response = client.post(
            "/api/calculate",
            json={
                "taxpayer_name": "Juan Pérez",
                "fiscal_year": 2024,
                "monthly_gross_income": 25000.0,
                "bonus_days": 15,
                "vacation_days": 12,
                "vacation_premium_percentage": 0.25,
                "general_deductions": 20000.0,
                "total_ppr": 10000.0,
                "total_tuition": 5000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields exist
        assert "gross_annual_income" in data
        assert "taxable_bonus" in data
        assert "taxable_vacation_premium" in data
        assert "total_taxable_income" in data
        assert "authorized_deductions" in data
        assert "taxable_base" in data
        assert "determined_tax" in data
        assert "withheld_tax" in data
        assert "balance_in_favor" in data
        assert "balance_to_pay" in data

    def test_calculation_with_default_values(self, client: TestClient):
        """Calculation works with minimal data (using defaults)"""
        response = client.post(
            "/api/calculate",
            json={
                "monthly_gross_income": 15000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["gross_annual_income"] > 0

    def test_zero_income_returns_zero_tax(self, client: TestClient):
        """Zero income should return zero tax"""
        response = client.post(
            "/api/calculate",
            json={
                "taxpayer_name": "Test User",
                "fiscal_year": 2024,
                "monthly_gross_income": 0.0,
                "bonus_days": 0,
                "vacation_days": 0,
                "vacation_premium_percentage": 0.0,
                "general_deductions": 0.0,
                "total_ppr": 0.0,
                "total_tuition": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["gross_annual_income"] == 0.0
        assert data["determined_tax"] == 0.0
        assert data["balance_in_favor"] == 0.0
        assert data["balance_to_pay"] == 0.0

    def test_high_income_calculation(self, client: TestClient):
        """High income calculation works correctly"""
        response = client.post(
            "/api/calculate",
            json={
                "taxpayer_name": "High Earner",
                "fiscal_year": 2024,
                "monthly_gross_income": 150000.0,
                "bonus_days": 30,
                "vacation_days": 20,
                "vacation_premium_percentage": 0.25,
                "general_deductions": 100000.0,
                "total_ppr": 50000.0,
                "total_tuition": 24500.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # High income should have higher tax
        assert data["determined_tax"] > 100000.0
        # Deductions should be capped at 5 UMAs
        uma_annual_2024 = 39606.36
        assert data["authorized_deductions"] <= uma_annual_2024 * 5 + 1

    def test_low_income_calculation(self, client: TestClient):
        """Low income calculation works correctly"""
        response = client.post(
            "/api/calculate",
            json={
                "taxpayer_name": "Low Earner",
                "fiscal_year": 2024,
                "monthly_gross_income": 8000.0,
                "bonus_days": 15,
                "vacation_days": 6,
                "vacation_premium_percentage": 0.25,
                "general_deductions": 5000.0,
                "total_ppr": 0.0,
                "total_tuition": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Low income should have low effective tax rate
        if data["total_taxable_income"] > 0:
            effective_rate = (
                data["determined_tax"] / data["total_taxable_income"]
            ) * 100
            assert effective_rate < 15.0


class TestFiscalYearValidation:
    """Tests for fiscal year validation"""

    def test_valid_fiscal_year_2024(self, client: TestClient):
        """2024 fiscal year should be accepted"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
            },
        )

        assert response.status_code == 200

    def test_valid_fiscal_year_2025(self, client: TestClient):
        """2025 fiscal year should be accepted"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2025,
                "monthly_gross_income": 20000.0,
            },
        )

        assert response.status_code == 200

    def test_valid_fiscal_year_2026(self, client: TestClient):
        """2026 fiscal year should be accepted"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2026,
                "monthly_gross_income": 20000.0,
            },
        )

        assert response.status_code == 200

    def test_invalid_fiscal_year_too_old(self, client: TestClient):
        """Fiscal year before 2024 should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2020,
                "monthly_gross_income": 20000.0,
            },
        )

        assert response.status_code == 422  # Validation error


class TestInputValidation:
    """Tests for input validation"""

    def test_negative_income_rejected(self, client: TestClient):
        """Negative income should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": -1000.0,
            },
        )

        assert response.status_code == 422

    def test_excessive_income_rejected(self, client: TestClient):
        """Income over 1,000,000 should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 2000000.0,
            },
        )

        assert response.status_code == 422

    def test_negative_bonus_days_rejected(self, client: TestClient):
        """Negative bonus days should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
                "bonus_days": -5,
            },
        )

        assert response.status_code == 422

    def test_excessive_bonus_days_rejected(self, client: TestClient):
        """Bonus days over 365 should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
                "bonus_days": 400,
            },
        )

        assert response.status_code == 422

    def test_negative_vacation_percentage_rejected(self, client: TestClient):
        """Negative vacation percentage should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
                "vacation_premium_percentage": -0.1,
            },
        )

        assert response.status_code == 422

    def test_vacation_percentage_over_1_rejected(self, client: TestClient):
        """Vacation percentage over 1 should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
                "vacation_premium_percentage": 1.5,
            },
        )

        assert response.status_code == 422

    def test_negative_deductions_rejected(self, client: TestClient):
        """Negative deductions should be rejected"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 20000.0,
                "general_deductions": -1000.0,
            },
        )

        assert response.status_code == 422


class TestDeductionCapping:
    """Tests for deduction cap behavior through API"""

    def test_deductions_capped_at_5_umas(self, client: TestClient):
        """Deductions should be capped at 5 UMAs for high income"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 200000.0,  # Very high income
                "general_deductions": 500000.0,
                "total_ppr": 300000.0,
                "total_tuition": 100000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 5 UMAs annual 2024 = 39606.36 * 5 = 198031.80
        uma_annual_2024 = 39606.36
        expected_cap = uma_annual_2024 * 5
        assert data["authorized_deductions"] == pytest.approx(expected_cap, rel=1e-2)

    def test_deductions_capped_at_15_percent(self, client: TestClient):
        """Deductions should be capped at 15% for lower income"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 15000.0,  # 180k annual, 15% = 27k
                "bonus_days": 0,
                "vacation_days": 0,
                "vacation_premium_percentage": 0.0,
                "general_deductions": 100000.0,
                "total_ppr": 50000.0,
                "total_tuition": 30000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 15% of 180k = 27k
        expected_cap = 180000.0 * 0.15
        assert data["authorized_deductions"] == pytest.approx(expected_cap, rel=1e-2)


class TestBonusAndVacationExemptions:
    """Tests for bonus and vacation premium exemptions through API"""

    def test_bonus_exemption_applied(self, client: TestClient):
        """Bonus exemption (30 UMAs) should be applied"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 30000.0,  # Daily = 1000
                "bonus_days": 15,  # Bonus = 15000
                "vacation_days": 0,
                "vacation_premium_percentage": 0.0,
                "general_deductions": 0.0,
                "total_ppr": 0.0,
                "total_tuition": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Bonus = 15000, exemption = 108.57 * 30 = 3257.10
        # Taxable bonus = 15000 - 3257.10 = 11742.90
        expected_taxable = 15000 - (108.57 * 30)
        assert data["taxable_bonus"] == pytest.approx(expected_taxable, rel=1e-2)

    def test_vacation_premium_exemption_applied(self, client: TestClient):
        """Vacation premium exemption (15 UMAs) should be applied"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 30000.0,  # Daily = 1000
                "bonus_days": 0,
                "vacation_days": 20,  # Premium = 1000 * 20 * 0.25 = 5000
                "vacation_premium_percentage": 0.25,
                "general_deductions": 0.0,
                "total_ppr": 0.0,
                "total_tuition": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Premium = 5000, exemption = 108.57 * 15 = 1628.55
        # Taxable = 5000 - 1628.55 = 3371.45
        expected_taxable = 5000 - (108.57 * 15)
        assert data["taxable_vacation_premium"] == pytest.approx(
            expected_taxable, rel=1e-2
        )


class TestResponseStructure:
    """Tests for API response structure"""

    def test_response_has_all_required_fields(self, client: TestClient):
        """Response should contain all required fields"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 25000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "gross_annual_income",
            "taxable_bonus",
            "taxable_vacation_premium",
            "total_taxable_income",
            "authorized_deductions",
            "personal_deductions",
            "ppr_deductions",
            "education_deductions",
            "taxable_base",
            "determined_tax",
            "withheld_tax",
            "balance_in_favor",
            "balance_to_pay",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_response_values_are_numbers(self, client: TestClient):
        """All response values should be numbers"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 25000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        for key, value in data.items():
            assert isinstance(value, (int, float)), (
                f"Field {key} should be numeric, got {type(value)}"
            )

    def test_response_values_non_negative(self, client: TestClient):
        """All response values should be non-negative"""
        response = client.post(
            "/api/calculate",
            json={
                "fiscal_year": 2024,
                "monthly_gross_income": 25000.0,
                "general_deductions": 50000.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        for key, value in data.items():
            assert value >= 0, f"Field {key} should be non-negative, got {value}"


class TestCrossYearConsistency:
    """Tests for consistency across fiscal years through API"""

    def test_same_input_different_years_different_results(self, client: TestClient):
        """Same input with different UMA values should give different results"""
        base_request = {
            "monthly_gross_income": 30000.0,
            "bonus_days": 15,
            "vacation_days": 12,
            "vacation_premium_percentage": 0.25,
            "general_deductions": 20000.0,
            "total_ppr": 10000.0,
            "total_tuition": 5000.0,
        }

        response_2024 = client.post(
            "/api/calculate", json={**base_request, "fiscal_year": 2024}
        )
        response_2026 = client.post(
            "/api/calculate", json={**base_request, "fiscal_year": 2026}
        )

        assert response_2024.status_code == 200
        assert response_2026.status_code == 200

        data_2024 = response_2024.json()
        data_2026 = response_2026.json()

        # 2026 has higher UMA, so more exemption, less taxable bonus
        assert data_2026["taxable_bonus"] < data_2024["taxable_bonus"]
