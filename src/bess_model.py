import numpy as np
import pandas as pd

class BatteryEnergyStorageSystem:
    """
    A class representing a Battery Energy Storage System (BESS)
    Default units for energy is kWh, for power is kW
    """
    def __init__(self, battery_capacity=4000, battery_power=2000, initial_soc=0.5, charging_efficiency=0.95,
                 discharging_efficiency=0.95, min_soc=0.1, max_soc=1):
        """
        Initialize the BESS with its characteristics

        Parameters:
        ------------
        battery_capacity : float
            Total energy capacity of the battery
        battery_power : float
            Maximum charge/discharge power of the battery
        initial_soc : float
            Initial state of charge as a fraction (0.0 to 1.0)
        charging_efficiency : float
            Efficiency of the charging process (0.0 to 1.0)
        discharging_efficiency : float
            Efficiency of the discharging process (0.1 to 1.0)
        min_soc : float
            Minimum allowed state of charge as a fraction, to prevent battery degradation
        max_soc : float
            Maximum allowed state of charge as a fraction
        """
        # Initialize the variables
        self.battery_capacity = battery_capacity
        self.battery_power = battery_power
        self.charging_efficiency = charging_efficiency
        self.discharging_efficiency = discharging_efficiency
        self.min_soc = min_soc
        self.max_soc = max_soc

        # Existing energy stored
        self.existing_energy = initial_soc * battery_capacity

        # Existing statef of charge
        self.soc = initial_soc

        # For tracking performances
        self.total_charged = 0      # Cumulative energy input to the battery
        self.total_discharged = 0   # Cumulative energy output from the battery
        self.total_losses = 0       # Cumulative energy lost due to inefficiencies

    def charge(self, charging_power, charging_time=1.0):
        """
        Charge the battery with the specific power for the given duration
        The default unit for charging_time is hour.

        Parameters:
        ------------
        charging_power : float
            Charging power in MW, must be a positive value
        charing_time : float
            Charing duration in hours

        Returns:
        ------------
        actual_charging_power : float
            Actual charging power used for charging the battery
        actual_charged_energy : float
            The amount of energy charged to the battery in the charing duration
        """

        if charging_power < 0:
            raise ValueError('Charging power must be positive!')
        
        # Limit charging power to battery's power rating
        actual_charging_power = min(charging_power, self.battery_power)

        # Calculate the energy that would be charged before efficiency losses
        charged_energy = actual_charging_power * charging_time

        # Apply charing efficiency
        actual_charged_energy = self.charging_efficiency * charged_energy

        # Check if this would exceed the battery's capacity
        charging_availability = self.max_soc * self.battery_capacity - self.existing_energy

        if actual_charged_energy > charging_availability:
            # Scale back the actual energy to not exceed capacity
            actual_charged_energy = charging_availability
        
        # Update battery state
        self.existing_energy = self.existing_energy + actual_charged_energy
        self.soc = self.existing_energy / self.battery_capacity

        # Track performance metrics
        self.total_charged = self.total_charged + actual_charged_energy
        self.total_losses = self.total_losses + charged_energy - actual_charged_energy

        return actual_charging_power, actual_charged_energy, self.existing_energy, self.soc
    
    def discharge(self, discharging_power, discharging_time=1.0):
        
        """
        Discharge the battery with the specified power for the given discharging time

        Parameters:
        ------------
        discharging_power
        discharging_time

        Returns:
        ------------
        actual_discharging_power
        actual_discharged_energy
        """

        if discharging_power < 0:
            raise ValueError('Discharging power must be positive!')
        
        # Limit discharging power to battery's power rating
        actual_discharging_power = min(discharging_power, self.battery_power)

        # Calculate the amount of energy discharged
        actual_discharged_energy = actual_discharging_power * discharging_time * self.discharging_efficiency

        # The discharged energy cannot be larger than the battery's energy availability
        discharging_availability = self.existing_energy - self.min_soc * self.battery_capacity
        if actual_discharged_energy > discharging_availability:
            actual_discharged_energy = discharging_availability
        
        # Update battery state
        self.existing_energy = self.existing_energy - actual_discharged_energy
        self.soc = self.existing_energy / self.battery_capacity

        # Track performance metrics
        self.total_discharged = self.total_discharged + actual_discharged_energy
        self.total_losses = self.total_losses + actual_discharging_power * discharging_time * (1 - self.discharging_efficiency)

        return actual_discharging_power, actual_discharged_energy, self.existing_energy, self.soc
    
    def get_battery_state(self):
        """
        Returns the battery state
        """
        return {
            'soc': self.soc,
            'existing energy': self.existing_energy,
            'total charged energy': self.total_charged,
            'total discharged energy': self.total_discharged,
            'total losses': self.total_losses
        }