import pandas as pd
import sys
import matplotlib.pyplot as plt
from datetime import datetime
import os

# -----------------------------
# 1. Input Data
# -----------------------------

weeks_open = 48
volunteer_class2 = False  # Set True to opt-in for Class 2 NIC if profit < £6,845

# -----------------------------
# 1b. Scenario Setup
# -----------------------------

scenarios = {
    # ----- Original Scenarios -----
    'Baseline': {  
        'no_show_rate': 0.10,  
        'appointment_fill_rate': 0.85,  
        'client_repeat_rate': 3.5  
    },  # Typical operations – 10% no-show, 85% fill rate, 3.5 visits per client

    'Growth': {  
        'no_show_rate': 0.05,  
        'appointment_fill_rate': 0.95,  
        'client_repeat_rate': 4.0  
    },  # High efficiency – 5% no-show, 95% fill rate, 4.0 visits per client

    'Stress test': {  
        'no_show_rate': 0.15,  
        'appointment_fill_rate': 0.75,  
        'client_repeat_rate': 2.5  
    },  # Challenging conditions – 15% no-show, 75% fill rate, 2.5 visits per client

    'Holiday': {  
        'no_show_rate': 0.25,  
        'appointment_fill_rate': 0.50,  
        'client_repeat_rate': 1.8  
    },  # Seasonal slowdown – 25% no-show, 50% fill rate, 1.8 visits per client

    'Marketing boost': {  
        'no_show_rate': 0.08,  
        'appointment_fill_rate': 0.90,  
        'client_repeat_rate': 5.0  
    },  # Successful campaign – 8% no-show, 90% fill rate, 5.0 visits per client

    'Referral program': {  
        'no_show_rate': 0.12,  
        'appointment_fill_rate': 0.88,  
        'client_repeat_rate': 4.5  
    },  # Word-of-mouth growth – 12% no-show, 88% fill rate, 4.5 visits per client

    # ----- New Scenarios -----
    'Weather disruption': {  
        'no_show_rate': 0.30,  
        'appointment_fill_rate': 0.60,  
        'client_repeat_rate': 2.0  
    },  # Severe weather – 30% no-show, 60% fill rate, 2.0 visits per client

    'Flu season': {  
        'no_show_rate': 0.18,  
        'appointment_fill_rate': 0.80,  
        'client_repeat_rate': 3.0  
    },  # Higher seasonal demand – 18% no-show, 80% fill rate, 3.0 visits per client

    'Economic downturn': {  
        'no_show_rate': 0.20,  
        'appointment_fill_rate': 0.65,  
        'client_repeat_rate': 2.2  
    },  # Reduced discretionary visits – 20% no-show, 65% fill rate, 2.2 visits per client

    'Tech upgrade': {  
        'no_show_rate': 0.07,  
        'appointment_fill_rate': 0.92,  
        'client_repeat_rate': 4.2  
    },  # Automation and reminders – 7% no-show, 92% fill rate, 4.2 visits per client

    'Weekend special': {  
        'no_show_rate': 0.15,  
        'appointment_fill_rate': 0.70,  
        'client_repeat_rate': 2.8  
    },  # Weekend availability – 15% no-show, 70% fill rate, 2.8 visits per client

    'Vip membership': {  
        'no_show_rate': 0.03,  
        'appointment_fill_rate': 0.98,  
        'client_repeat_rate': 6.0  
    },  # Premium loyalty – 3% no-show, 98% fill rate, 6.0 visits per client

    'New competitor': {  
        'no_show_rate': 0.14,  
        'appointment_fill_rate': 0.72,  
        'client_repeat_rate': 2.7  
    },  # Market share loss – 14% no-show, 72% fill rate, 2.7 visits per client

    'Staff shortage': {  
        'no_show_rate': 0.12,  
        'appointment_fill_rate': 0.55,  
        'client_repeat_rate': 2.4  
    },  # Reduced capacity – 12% no-show, 55% fill rate, 2.4 visits per client

    'Social media campaign': {  
        'no_show_rate': 0.10,  
        'appointment_fill_rate': 0.93,  
        'client_repeat_rate': 4.8  
    },  # Online buzz – 10% no-show, 93% fill rate, 4.8 visits per client
}

# -----------------------------
# Clinic Configurations
# -----------------------------

clinic_hours = {
    'Vista Clinic': {'days': ['Monday'], 'start': '10:00', 'end': '20:00'},
    'Niks Skin': {'days': ['Wednesday', 'Thursday'], 'start': '09:30', 'end': '20:00'},
    'Jaydes Spa': {'days': ['Friday'], 'start': '10:00', 'end': '20:00'}
}

clinic_totals = {
    'Vista Clinic': 3, # patients
    'Niks Skin': 11,   # patients 
    'Jaydes Spa': 10   # patients 
}

clinic_rent = {
    'Vista Clinic': {'amount': 65.0, 'type': 'weekly'},
    'Niks Skin': {'amount': 140.0, 'type': 'weekly'},
    'Jaydes Spa': {'amount': 65.0, 'type': 'weekly'}
}

fixed_costs = {
    'Vista Clinic': 5.0,
    'Niks Skin': 0.0,
    'Jaydes Spa': 5.0
}

payment_fee_percent = 1.75 / 100
payment_fee_fixed = 0.20
consumable_cost_per_patient = 1.0

services = {
    'Vista Clinic': [
        {'service': 'Sports Massage 30m', 'duration': 30, 'price': 40.0, 'popularity': 0.25},
        {'service': 'Sports Massage 60m', 'duration': 60, 'price': 70.0, 'popularity': 0.25},
        {'service': 'Sports Therapy 30m', 'duration': 30, 'price': 40.0, 'popularity': 0.25},
        {'service': 'Sports Therapy 60m', 'duration': 60, 'price': 70.0, 'popularity': 0.25},
    ],
    'Niks Skin': [
        {'service': 'Baby & Me 30m', 'duration': 30, 'price': 40.0, 'popularity': 0.1},
        {'service': 'Dry Needling 1 Area 30m', 'duration': 30, 'price': 40.0, 'popularity': 0.1},
        {'service': 'Dry Needling 2 Areas 45m', 'duration': 45, 'price': 50.0, 'popularity': 0.2},
        {'service': 'Sports Therapy 1ST CON 60m', 'duration': 60, 'price': 70.0, 'popularity': 0.2},
        {'service': 'MYOFASCIAL DRY CUPPING (1 AREA)', 'duration': 30, 'price': 40.0, 'popularity': 0.1},
        {'service': 'MYOFASCIAL DRY CUPPING (FULL BODY)', 'duration': 60, 'price': 70.0, 'popularity': 0.1},
        {'service': 'Put Your Hands In The Air 30m', 'duration': 30, 'price': 40.0, 'popularity': 0.05},
        {'service': 'Run Down Legs', 'duration': 30, 'price': 40.0, 'popularity': 0.05},
        {'service': 'SPORTS THERAPY TREATMENT 30 Minutes', 'duration': 30, 'price': 40.0, 'popularity': 0.05},
        {'service': 'That time of the month', 'duration': 30, 'price': 40.0, 'popularity': 0.05},
    ],
    'Jaydes Spa': [
        {'service': 'Full Body MOT 60m (Public)', 'duration': 60, 'price': 75.0, 'popularity': 0.10},
        {'service': 'Full Body MOT 60m (Resident)', 'duration': 60, 'price': 67.50, 'popularity': 0.10},
        {'service': 'The Posture Reset 30m (Public)', 'duration': 30, 'price': 45.0, 'popularity': 0.08},
        {'service': 'The Posture Reset 30m (Resident)', 'duration': 30, 'price': 40.50, 'popularity': 0.08},
        {'service': 'Run-Down Legs 30m (Public)', 'duration': 30, 'price': 45.0, 'popularity': 0.08},
        {'service': 'Run-Down Legs 30m (Resident)', 'duration': 30, 'price': 40.50, 'popularity': 0.08},
        {'service': 'Put Your Hands In The Air 30m (Public)', 'duration': 30, 'price': 45.0, 'popularity': 0.08},
        {'service': 'Put Your Hands In The Air 30m (Resident)', 'duration': 30, 'price': 40.50, 'popularity': 0.08},
        {'service': 'That Time of the Month 30m (Public)', 'duration': 30, 'price': 45.0, 'popularity': 0.07},
        {'service': 'That Time of the Month 30m (Resident)', 'duration': 30, 'price': 40.50, 'popularity': 0.07},
        {'service': 'Baby & Me 30m (Public)', 'duration': 30, 'price': 45.0, 'popularity': 0.07},
        {'service': 'Baby & Me 30m (Resident)', 'duration': 30, 'price': 40.50, 'popularity': 0.07},
    ]
}

# -----------------------------
# 2. Helper Functions
# -----------------------------

def get_weekly_rent(clinic):
    rent_info = clinic_rent[clinic]
    if rent_info['type'] == 'weekly':
        return rent_info['amount']
    elif rent_info['type'] == 'daily':
        return rent_info['amount'] * len(clinic_hours[clinic]['days'])
    elif rent_info['type'] == 'annual':
        return rent_info['amount'] / weeks_open
    else:
        raise ValueError("Unknown rent type")

def get_annual_rent(clinic):
    return get_weekly_rent(clinic) * weeks_open

def get_weekly_hours(clinic):
    start = datetime.strptime(clinic_hours[clinic]['start'], '%H:%M')
    end = datetime.strptime(clinic_hours[clinic]['end'], '%H:%M')
    daily = (end - start).seconds / 3600
    return daily * len(clinic_hours[clinic]['days'])

def calculate_service_profit(service, clinic_name):
    total_patients_week = clinic_totals[clinic_name]
    patients = total_patients_week * service['popularity'] * (1 - no_show_rate)

    revenue = patients * service['price'] * weeks_open
    payment_cost = revenue * payment_fee_percent + (patients * weeks_open * payment_fee_fixed)
    consumables = patients * weeks_open * consumable_cost_per_patient
    variable_cost = payment_cost + consumables
    profit = revenue - variable_cost

    hours = patients * (service['duration'] / 60) * weeks_open
    revenue_per_hour = revenue / hours if hours > 0 else 0
    revenue_per_client = revenue / (patients * weeks_open / client_repeat_rate) if patients > 0 else 0

    return {
        'Service': service['service'],
        'Duration (min)': service['duration'],
        'Patients/Week': patients,
        'Annual Revenue': revenue,
        'Variable Cost': variable_cost,
        'Profit': profit,
        'Profit per Hour': profit / hours if hours > 0 else 0,
        'Revenue per Hour': revenue_per_hour,
        'Revenue per Client': revenue_per_client
    }

def calculate_tax(profit):
    tax_free = 12570
    profit_taxable = max(0, profit - tax_free)
    income_tax = 0
    if profit_taxable <= 37700:
        income_tax += profit_taxable * 0.20
    else:
        income_tax += 37700 * 0.20
        if profit_taxable <= 112570:
            income_tax += (profit_taxable - 37700) * 0.40
        else:
            income_tax += (112570 - 37700) * 0.40
            income_tax += (profit_taxable - 112570) * 0.45

    class4 = 0
    if profit > 12570:
        band = min(profit, 50270) - 12570
        class4 += band * 0.06
        if profit > 50270:
            class4 += (profit - 50270) * 0.02

    class2 = 0
    if profit < 6845 and volunteer_class2:
        class2 = 3.50 * weeks_open

    total_tax = income_tax + class4 + class2
    return {
        'Income Tax': income_tax,
        'Class 4 NICs': class4,
        'Class 2 NICs': class2,
        'Total Tax': total_tax,
        'Net Profit': profit - total_tax,
        'Net Margin %': ((profit - total_tax) / profit * 100) if profit > 0 else 0
    }

def break_even_patients(clinic_name, avg_price, avg_var_cost):
    weekly_fixed = get_weekly_rent(clinic_name) + fixed_costs[clinic_name]
    unit_margin = avg_price - avg_var_cost
    return float('inf') if unit_margin <= 0 else weekly_fixed / unit_margin

def calculate_clinic(clinic_name):
    clinic_services = services[clinic_name]
    df_services = pd.DataFrame([calculate_service_profit(s, clinic_name) for s in clinic_services])
    total_revenue = df_services['Annual Revenue'].sum()
    total_variable = df_services['Variable Cost'].sum()
    total_fixed = get_annual_rent(clinic_name) + fixed_costs[clinic_name] * weeks_open
    gross_profit = total_revenue - total_variable - total_fixed
    booked_hours = df_services.apply(lambda r: r['Patients/Week'] * (r['Duration (min)'] / 60), axis=1).sum()
    available_hours = get_weekly_hours(clinic_name) * appointment_fill_rate
    utilization = (booked_hours / available_hours * 100) if available_hours > 0 else 0
    capacity = "OVERBOOKED" if booked_hours > available_hours else "OK"
    avg_price = total_revenue / (clinic_totals[clinic_name] * weeks_open)
    avg_var_cost = total_variable / (clinic_totals[clinic_name] * weeks_open)
    break_even = break_even_patients(clinic_name, avg_price, avg_var_cost)
    tax_data = calculate_tax(gross_profit)
    return df_services, {
        'Clinic': clinic_name,
        'Annual Revenue': total_revenue,
        'Variable Costs': total_variable,
        'Fixed Costs': total_fixed,
        'Gross Profit': gross_profit,
        **tax_data,
        'Weekly Hours Available': available_hours,
        'Weekly Hours Booked': booked_hours,
        'Utilization %': utilization,
        'Capacity Status': capacity,
        'Weekly Break-Even Patients': break_even
    }

def simulate_yoy_growth(clinic_name, base_profit, years=5, annual_growth_rate=0.05):
    data = []
    for year in range(1, years + 1):
        growth_multiplier = (1 + annual_growth_rate) ** (year - 1)
        data.append({
            'Year': f'Year {year}',
            'Projected Revenue': base_profit['Annual Revenue'] * growth_multiplier,
            'Projected Profit': base_profit['Net Profit'] * growth_multiplier
        })
    return pd.DataFrame(data)

def calculate_cash_flow(clinic_summary):
    monthly_profit = clinic_summary['Net Profit'] / 12
    cumulative_cash = []
    cash = 0
    for m in range(1, 13):
        cash += monthly_profit
        cumulative_cash.append({'Month': f'Month {m}', 'Cumulative Cash': cash})
    return pd.DataFrame(cumulative_cash)

def run_price_sensitivity(clinic_name, price_adjustments=[-0.1, 0.0, 0.1]):
    results = []
    original_services = services[clinic_name]

    for adj in price_adjustments:
        adjusted_services = []
        for s in original_services:
            s_copy = s.copy()
            s_copy['price'] = s['price'] * (1 + adj)
            adjusted_services.append(s_copy)

        services[clinic_name] = adjusted_services  # temporarily override
        _, summary = calculate_clinic(clinic_name)
        results.append({
            'Adjustment': f"{int(adj*100)}%",
            'Revenue': summary['Annual Revenue'],
            'Net Profit': summary['Net Profit']
        })

    services[clinic_name] = original_services  # restore
    return pd.DataFrame(results)

def get_utilization_summary(df_summary):
    return df_summary[['Clinic', 'Weekly Hours Available', 'Weekly Hours Booked', 'Utilization %']]

# -----------------------------
# 3. Main Scenario Runner
# -----------------------------

def run_scenario(
    scenario_arg,
    export_excel=True,
    generate_plots=True,
    return_dataframes=True,
    clinic_totals_override=None  # ✅ Added
):
    if scenario_arg not in scenarios:
        raise ValueError(f"Invalid scenario '{scenario_arg}'. Choose from {list(scenarios.keys())}.")

    global no_show_rate, appointment_fill_rate, client_repeat_rate
    selected_scenario = scenarios[scenario_arg]
    no_show_rate = selected_scenario['no_show_rate']
    appointment_fill_rate = selected_scenario['appointment_fill_rate']
    client_repeat_rate = selected_scenario['client_repeat_rate']

    # ✅ Prepare working copy of clinic totals
    working_clinic_totals = clinic_totals.copy()
    if clinic_totals_override:
        for clinic in working_clinic_totals:
            if clinic in clinic_totals_override:
                working_clinic_totals[clinic] = clinic_totals_override[clinic]

    all_services = []
    clinic_summaries = []

    for clinic in services:
        # Temporarily patch global for calculations
        original_value = clinic_totals[clinic]
        clinic_totals[clinic] = working_clinic_totals[clinic]

        df, summary = calculate_clinic(clinic)
        df['Clinic'] = clinic
        all_services.append(df)
        clinic_summaries.append(summary)

        # Restore original global
        clinic_totals[clinic] = original_value

    df_services_all = pd.concat(all_services, ignore_index=True)
    df_summary = pd.DataFrame(clinic_summaries)

    # Additional DataFrames
    growth_outputs, cash_flows, price_sensitivity_all = [], [], []
    for summary in clinic_summaries:
        df_growth = simulate_yoy_growth(summary['Clinic'], summary)
        df_growth['Clinic'] = summary['Clinic']
        growth_outputs.append(df_growth)

        df_cash = calculate_cash_flow(summary)
        df_cash['Clinic'] = summary['Clinic']
        cash_flows.append(df_cash)

        df_price = run_price_sensitivity(summary['Clinic'])
        df_price['Clinic'] = summary['Clinic']
        price_sensitivity_all.append(df_price)

    df_growth_all = pd.concat(growth_outputs, ignore_index=True)
    df_cashflow_all = pd.concat(cash_flows, ignore_index=True)
    df_price_all = pd.concat(price_sensitivity_all, ignore_index=True)
    utilization_df = df_summary[['Clinic', 'Weekly Hours Available', 'Weekly Hours Booked', 'Utilization %']]

    # Excel export
    if export_excel:
        output_filename = f'clinic_profitability_{scenario_arg}.xlsx'
        with pd.ExcelWriter(output_filename) as writer:
            df_services_all.to_excel(writer, sheet_name='Services', index=False)
            df_summary.to_excel(writer, sheet_name='Clinic Summary', index=False)
            df_growth_all.to_excel(writer, sheet_name='YoY Growth', index=False)
            df_cashflow_all.to_excel(writer, sheet_name='Cash Flow', index=False)
            df_price_all.to_excel(writer, sheet_name='Price Sensitivity', index=False)
            utilization_df.to_excel(writer, sheet_name='Utilization', index=False)

    # Plot generation (optional for Streamlit)
    if generate_plots:
        fig, ax = plt.subplots()
        clinics = df_summary['Clinic']
        actual_patients = [working_clinic_totals[c] for c in clinics]
        break_even_patients_list = df_summary['Weekly Break-Even Patients']

        x = range(len(clinics))
        bar_width = 0.35
        ax.bar(x, actual_patients, width=bar_width, label='Actual Patients')
        ax.bar([i + bar_width for i in x], break_even_patients_list, width=bar_width, label='Break-Even Patients')
        ax.set_xlabel('Clinic')
        ax.set_ylabel('Patients per Week')
        ax.set_title(f'Break-Even vs Actual Patients ({scenario_arg} scenario)')
        ax.set_xticks([i + bar_width / 2 for i in x])
        ax.set_xticklabels(clinics)
        ax.legend()
        plt.tight_layout()
        plot_filename = f'break_even_comparison_{scenario_arg}.png'
        plt.savefig(plot_filename)

    # Return DataFrames for Streamlit
    if return_dataframes:
        return {
            "services": df_services_all,
            "summary": df_summary,
            "growth": df_growth_all,
            "cash_flow": df_cashflow_all,
            "price_sensitivity": df_price_all,
            "utilization": utilization_df
        }

# -----------------------------
# 4. Interactive CLI
# -----------------------------

if __name__ == "__main__":
    while True:
        print("\n=== Clinic Profitability Scenario Runner ===")
        print("Choose a scenario to run:")
        for i, name in enumerate(scenarios.keys(), start=1):
            print(f"{i}. {name}")
        print("0. Exit")

        choice = input("Enter your choice (number): ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        try:
            index = int(choice) - 1
            scenario_name = list(scenarios.keys())[index]
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"\nRunning scenario: {scenario_name}\n")
            run_scenario(scenario_name)
        except (ValueError, IndexError):
            print("Invalid choice. Please try again.")
