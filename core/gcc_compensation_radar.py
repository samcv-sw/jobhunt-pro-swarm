"""
GCC Executive Compensation & Benchmarking Radar
JobHunt Pro SaaS - In-depth breakdown of base salary, allowances, EOSB, and net savings.
"""
from typing import Dict, List, Any, Optional


class GccCompensationRadar:
    """
    Computes comprehensive executive compensation packages across Saudi Arabia, UAE, and Qatar.
    """

    COMPANY_BENCHMARKS = {
        "aramco": {
            "name": "Saudi Aramco / Energy Tech",
            "base_multiplier": 1.25,
            "housing_months": 3,
            "transport_rate": 0.10,
            "schooling_per_child_sar": 35000,
            "bonus_target_months": 3.5,
            "currency": "SAR"
        },
        "neom": {
            "name": "NEOM Mega Projects",
            "base_multiplier": 1.35,
            "housing_months": 3.5,
            "transport_rate": 0.12,
            "schooling_per_child_sar": 45000,
            "bonus_target_months": 3.0,
            "currency": "SAR"
        },
        "emirates_tech": {
            "name": "Emirates Group / Dubai Future Labs",
            "base_multiplier": 1.20,
            "housing_months": 3.0,
            "transport_rate": 0.10,
            "schooling_per_child_sar": 30000,
            "bonus_target_months": 2.5,
            "currency": "AED"
        },
        "alrajhi": {
            "name": "Al Rajhi Bank / Fintech",
            "base_multiplier": 1.15,
            "housing_months": 3.0,
            "transport_rate": 0.10,
            "schooling_per_child_sar": 25000,
            "bonus_target_months": 4.0,
            "currency": "SAR"
        }
    }

    @classmethod
    def compute_full_package(
        cls,
        basic_salary: float,
        company_key: str = "aramco",
        years_of_service: int = 5,
        num_children: int = 2,
        estimated_monthly_expenses: float = 12000.0
    ) -> Dict[str, Any]:
        """
        Calculates granular breakdown of allowances, annual cash total, EOSB, and net annual savings.
        """
        benchmark = cls.COMPANY_BENCHMARKS.get(company_key, cls.COMPANY_BENCHMARKS["aramco"])
        curr = benchmark["currency"]

        # Allowances
        monthly_housing = (basic_salary * benchmark["housing_months"]) / 12.0
        monthly_transport = basic_salary * benchmark["transport_rate"]
        monthly_gross = basic_salary + monthly_housing + monthly_transport

        # Annual Add-ons
        annual_schooling = num_children * benchmark["schooling_per_child_sar"]
        annual_bonus = basic_salary * benchmark["bonus_target_months"]
        annual_flight_tickets = (2 + num_children) * 3500.0  # SAR/AED per ticket estimate

        total_annual_cash = (monthly_gross * 12.0) + annual_schooling + annual_bonus + annual_flight_tickets

        # End of Service Gratuity (Saudi Labor Law Article 84)
        if years_of_service <= 5:
            total_eosb = years_of_service * (basic_salary * 0.5)
        else:
            first_5_years = 5 * (basic_salary * 0.5)
            remaining_years = (years_of_service - 5) * basic_salary
            total_eosb = first_5_years + remaining_years

        # Net Annual Savings
        annual_expenses = estimated_monthly_expenses * 12.0
        net_annual_savings = max(0.0, total_annual_cash - annual_expenses)

        return {
            "company_name": benchmark["name"],
            "currency": curr,
            "monthly_breakdown": {
                "basic_salary": round(basic_salary, 2),
                "housing_allowance": round(monthly_housing, 2),
                "transport_allowance": round(monthly_transport, 2),
                "total_monthly_gross": round(monthly_gross, 2)
            },
            "annual_benefits": {
                "schooling_allowance": round(annual_schooling, 2),
                "performance_bonus_target": round(annual_bonus, 2),
                "annual_family_tickets": round(annual_flight_tickets, 2),
                "total_annual_cash_package": round(total_annual_cash, 2)
            },
            "end_of_service_gratuity": {
                "years_of_service": years_of_service,
                "total_eosb_payout": round(total_eosb, 2),
                "law_reference": "Article 84 Saudi / UAE Federal Decree No. 33"
            },
            "financial_health": {
                "estimated_annual_expenses": round(annual_expenses, 2),
                "net_annual_savings_potential": round(net_annual_savings, 2),
                "savings_rate_percentage": round((net_annual_savings / max(1.0, total_annual_cash)) * 100.0, 1)
            }
        }


# Global singleton instance
gcc_compensation_radar = GccCompensationRadar()
