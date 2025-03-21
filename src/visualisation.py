def visualize_results(results):
    """
    Create visualizations of the simulation results
    
    Parameters:
    -----------
    results : pandas.DataFrame
        Simulation results
            
    Returns:
    --------
    tuple : Figures for the visualizations
    """
    # Set Seaborn style
    sns.set_style("whitegrid")
    
    # Figure 1: Power flows over time (a week)
    week_data = results.iloc[0:168]  # First week
    
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    
    ax1.plot(week_data['timestamp'], week_data['pv_generation_mw'], 'y-', label='PV Generation')
    ax1.plot(week_data['timestamp'], week_data['building_demand_mw'], 'r-', label='Building Demand')
    ax1.plot(week_data['timestamp'], week_data['battery_power_mw'], 'g-', label='Battery Power')
    ax1.plot(week_data['timestamp'], week_data['grid_power_mw'], 'b-', label='Grid Power')
    
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.2)
    ax1.set_title('Power Flows - First Week', fontsize=16)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Power (MW)', fontsize=12)
    ax1.legend(fontsize=12)
    ax1.grid(True)
    
    # Format x-axis dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H'))
    fig1.autofmt_xdate()
    
    # Figure 2: Battery state of charge over time
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    
    # Create a colormap for SOC
    cmap = plt.cm.viridis
    norm = plt.Normalize(vmin=0, vmax=1)
    
    # Plot battery SOC with color indicating level
    for i in range(1, len(results)):
        ax2.plot(results['timestamp'].iloc[i-1:i+1], 
                 results['battery_soc'].iloc[i-1:i+1], 
                 color=cmap(norm(results['battery_soc'].iloc[i])))
    
    ax2.set_title('Battery State of Charge (SOC)', fontsize=16)
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('State of Charge', fontsize=12)
    ax2.grid(True)
    ax2.set_ylim(0, 1)
    
    # Add a colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2)
    cbar.set_label('State of Charge', fontsize=12)
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig2.autofmt_xdate()
    
    # Figure 3: Monthly summary
    monthly_data = results.resample('M', on='timestamp').sum()
    monthly_soc = results.resample('M', on='timestamp').mean()['battery_soc']
    
    fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    
    # Monthly energy flow
    monthly_data['grid_import_mwh'] = monthly_data.loc[monthly_data['grid_power_mw'] > 0, 'grid_power_mw']
    monthly_data['grid_export_mwh'] = -monthly_data.loc[monthly_data['grid_power_mw'] < 0, 'grid_power_mw']
    monthly_data['battery_charge_mwh'] = monthly_data.loc[monthly_data['battery_power_mw'] > 0, 'battery_power_mw']
    monthly_data['battery_discharge_mwh'] = -monthly_data.loc[monthly_data['battery_power_mw'] < 0, 'battery_power_mw']
    
    # Plot monthly energy
    index = np.arange(len(monthly_data.index))
    bar_width = 0.35
    
    ax3a.bar(index, monthly_data['pv_generation_mw'], bar_width, label='PV Generation')
    ax3a.bar(index, monthly_data['building_demand_mw'], bar_width, label='Building Demand')
    ax3a.bar(index + bar_width, monthly_data['grid_import_mwh'], bar_width, label='Grid Import')
    ax3a.bar(index + bar_width, monthly_data['grid_export_mwh'], bar_width, label='Grid Export')
    
    ax3a.set_title('Monthly Energy Flows', fontsize=16)
    ax3a.set_ylabel('Energy (MWh)', fontsize=12)
    ax3a.legend(fontsize=12)
    ax3a.grid(True)
    ax3a.set_xticks(index + bar_width / 2)
    ax3a.set_xticklabels([d.strftime('%b %Y') for d in monthly_data.index], rotation=45)
    
    # Plot monthly battery activity
    ax3b.bar(index, monthly_data['battery_charge_mwh'], bar_width, label='Battery Charge')
    ax3b.bar(index + bar_width, monthly_data['battery_discharge_mwh'], bar_width, label='Battery Discharge')
    ax3b.plot(index + bar_width/2, monthly_soc.values, 'ko-', label='Average SOC')
    
    ax3b.set_title('Monthly Battery Activity', fontsize=16)
    ax3b.set_xlabel('Month', fontsize=12)
    ax3b.set_ylabel('Energy (MWh) / SOC', fontsize=12)
    ax3b.legend(fontsize=12)
    ax3b.grid(True)
    ax3b.set_xticks(index + bar_width / 2)
    ax3b.set_xticklabels([d.strftime('%b %Y') for d in monthly_data.index], rotation=45)
    
    fig3.tight_layout()
    
    # Figure 4: Summary statistics
    fig4, ax4 = plt.subplots(figsize=(10, 8))
    
    summary_labels = ['PV Generation', 'Building Demand', 'Grid Import', 'Grid Export', 
                     'Battery Charge', 'Battery Discharge', 'Battery Losses']
    summary_values = [analysis['total_pv_generation_mwh'], 
                      analysis['total_building_demand_mwh'],
                      analysis['total_grid_import_mwh'], 
                      analysis['total_grid_export_mwh'],
                      analysis['total_charged_mwh'], 
                      analysis['total_discharged_mwh'],
                      analysis['total_losses_mwh']]
    
    ax4.bar(summary_labels, summary_values)
    ax4.set_title('Annual Energy Summary', fontsize=16)
    ax4.set_ylabel('Energy (MWh)', fontsize=12)
    ax4.grid(True, axis='y')
    
    for i, v in enumerate(summary_values):
        ax4.text(i, v + 0.1, f'{v:.1f}', ha='center')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add summary text
    summary_text = (
        f"Battery Cycles: {analysis['battery_cycles']:.2f}\n"
        f"Overall Efficiency: {analysis['overall_efficiency']*100:.2f}%\n"
        f"Total Losses: {analysis['total_losses_mwh']:.2f} MWh\n"
        f"Net Electricity Cost: ${analysis['net_electricity_cost']:.2f}\n"
        f"Estimated Savings: ${analysis['estimated_savings']:.2f}"
    )
    
    plt.figtext(0.7, 0.02, summary_text, fontsize=12, 
                bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
    
    return fig1, fig2, fig3, fig4