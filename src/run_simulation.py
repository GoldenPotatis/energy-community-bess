import numpy as np
import pandas as pd

def run_simulation(battery, pv_generation, building_demand, electricity_prices,
                   control_strategy='simple', grid_connection_limit=None):
    """
    Run the simulation of the BESS for a full year

    Parameters:
    ------------
    battery : BatterEnergyStorageSystem
        The battery instance to simulate
    pv_generation : pandas.Series
        Hourly PV generation in kW
    building_demand: pandas.Series
        Hourly building electricity demand in kW
    electricity_prices : pandas.Series
        Hourly electricity price
    control_strategy : str
        Strategy to control bettery operation:
        - 'simple' : Charge from excess PV, discharge to meet demand
        - 'price_arbitrage' : Also consider electricity prices for operation
    grid_connection_limit : float or None
        Maximum power that can be imported/exported from the grid
    """

    # Check that all input series have the same length
    if not (len(pv_generation) == len(building_demand) == len(electricity_prices)):
        raise ValueError('Input data series must have the same length!')
    
    # Prepare the results DataFrame
    results = pd.DataFrame({
        'timestamp': pv_generation.index,
        'pv_generation': pv_generation.values,
        'building_demand': building_demand.values,
        'electricity_prices': electricity_prices.values
    })

    # Arrays to store simulation results
    # The difference between PV generation and building demand
    net_load = pv_generation - building_demand
    energy_movement = np.zeros(len(net_load))
    battery_soc = np.zeros(len(net_load))
    battery_energy = np.zeros(len(net_load))
    grid_power = np.zeros(len(net_load))
    electricity_cost = np.zeros(len(net_load))

    # Run simulation hour by hour
    for hour in range(len(net_load)):
        current_net_load = net_load.iloc[hour]
        current_price = electricity_prices.iloc[hour]

        # Determine battery operation based on strategy
        if control_strategy == 'simple':
            if current_net_load > 0: # PV can cover building demand, excess PV generation
                # Charge the battery with excess PV
                charging_power = current_net_load
                actual_charged_energy = battery.charge(charging_power)[1]
                energy_movement[hour] = actual_charged_energy # Positive is charging
                battery_energy[hour] = battery.get_battery_state()['existing energy']
                battery_soc[hour] = battery.get_battery_state()['soc']
                # If there is still excess PV generation, then export it to grid
                remaining_PV = current_net_load - actual_charged_energy
                grid_power[hour] = remaining_PV # Export to the grid
                
            else: # PV cannot cover building demand
                  # Try to discharge battery first to cover building demand
                discharging_power = - current_net_load # Convert it to positive values
                actual_discharged_energy = battery.discharge(discharging_power)[1]
                energy_movement[hour] = - actual_discharged_energy # Negative means discharging
                battery_energy[hour] = battery.get_battery_state()['existing energy']
                battery_soc[hour] = battery.get_battery_state()['soc']
                # If battery is dificit, then import electricity from the grid
                remaining_dificit = current_net_load + actual_discharged_energy
                grid_power[hour] = remaining_dificit # Import from the grid
        elif control_strategy == 'price arbitrage':
            # Simplified price threshold logic
            # In a real implementation, you would use more sophisticated logic
            price_threshold_low = np.percentile(electricity_prices, 25)
            price_threshold_high = np.percentile(electricity_prices, 75)

            if current_price <= price_threshold_low:
                # Low price means good time to charge
                # But still prioritize using excess PV to charge first because it's free
                if current_net_load > 0:
                    # We have excess PV, use it first
                    charging_power = current_net_load
                else:
                    # No excess PV but price is low, so consider charing from grid
                    # You can choose to charge battery to full or
                    # Only charge from grid if batttery is below 70% SOC
                    # Here we choose to charge battery to full
                    charging_power = battery.battery_power
            
                actual_charged_energy = battery.charge(charging_power)
                energy_movement[hour] = actual_charged_energy # Positive is charging
                battery_energy[hour] = battery.get_battery_state()['existing energy']
                battery_soc[hour] = battery.get_battery_state()['soc']
                # If there is still excess PV generation, then export it to grid
                remaining_PV = current_net_load - actual_charged_energy
                grid_power[hour] = remaining_PV # Export to the grid

            if current_price > price_threshold_high:
                # High price means good time to discharge
                if current_net_load < 0:
                    # PV not enough to cover building load therefore discharge the battery
                    discharging_power = - current_net_load # convert to positive value
                else:
                    # PV enough to cover building load, but price is high, so dicharge to the grid
                    # You can choose to dischagre batter to SOC=0.1 or
                    # Only discharge to grid if battery is above SOC=0.3
                    # Here we choose to discharge batter to SOC=0.1
                    if battery.soc > 0.1:
                        discharging_power = battery.batter_power
                    else:
                        discharging_power = 0
                
                actual_discharged_energy = battery.discharge(discharging_power)
                energy_movement[hour] = - actual_discharged_energy # Negative is discharging
                battery_energy[hour] = battery.get_battery_state()['existing energy']
                battery_soc[hour] = battery.get_battery_state()['soc']
                # If battery is dificit, then import electricity from the grid
                remaining_dificit = current_net_load + actual_discharged_energy
                grid_power[hour] = remaining_dificit # Import from the grid

            else:
                # Medium price, the operate normally like in 'simple' strategy
                if current_net_load > 0: # PV can cover building demand, excess PV generation
                    # Charge the battery with excess PV
                    charging_power = current_net_load
                    actual_charged_energy = battery.charge(charging_power)[1]
                    energy_movement[hour] = actual_charged_energy # Positive is charging
                    battery_energy[hour] = battery.get_battery_state()['existing energy']
                    battery_soc[hour] = battery.get_battery_state()['soc']
                    # If there is still excess PV generation, then export it to grid
                    remaining_PV = current_net_load - actual_charged_energy
                    grid_power[hour] = remaining_PV # Export to the grid
                
                else: # PV cannot cover building demand
                    # Try to discharge battery first to cover building demand
                    discharging_power = current_net_load
                    actual_discharged_energy = battery.discharge(discharging_power)[1]
                    energy_movement[hour] = - actual_discharged_energy # Negative means discharging
                    battery_energy[hour] = battery.get_battery_state()['existing energy']
                    battery_soc[hour] = battery.get_battery_state()['soc']
                    # If battery is dificit, then import electricity from the grid
                    remaining_dificit = current_net_load + actual_discharged_energy
                    grid_power[hour] = remaining_dificit # Import from the grid

        # Apply grid connection limit if specified
        if grid_connection_limit is not None:
            pass

        # Calculate cost/revenue from electricity exchange with grid
        electricity_cost[hour] = grid_power[hour] * current_price

        # Store battery state
        battery_state = battery.get_battery_state()
    
    # Add results to DataFrame
    results['energy_movement'] = energy_movement
    results['battery_soc'] = battery_soc
    results['battery_energy'] = battery_energy
    results['grid_power'] = grid_power
    results['electricity_cost'] = electricity_cost
    
    return results



    


