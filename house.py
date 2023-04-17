# FIND BETTER CITATIONS
natural_gas_energy_density = 53.6e6 # J/kg --  https://en.wikipedia.org/wiki/Energy_density
air_volumetric_heat_capacity = 1210 # https://en.wikipedia.org/wiki/Table_of_specific_heat_capacities
inches_to_meters = 0.0254

# Behaviour values
HEATER = 1
AIR_CONDITIONER = -1
OTHER = 0

class House:
    def __init__(self, internal_temp, external_temp):
        self.storeys = []
        self.surfaces = []
        self.internal_temp = internal_temp
        self.external_temp = external_temp
        self.appliances = []

    def add_surface(self, *args):
        self.surfaces.extend(args)
    
    def add_appliance(self, *args):
        self.appliances.extend(args)

    def volume(self):
        V_tot = 0
        for storey in self.storeys:
            V_tot += storey[0] * storey[1]
        return V_tot
    
    def gross_floor_area(self):
        A_tot = 0
        for storey in self.storeys:
            A_tot += storey[0]
        # for i in range(len(self.storeys) - 1): # Exclude attic
        #     A_tot += self.storeys[i][0]
        return A_tot

    def Q(self):
        Q_tot = 0
        for wall in self.surfaces:
            Q_tot += wall.Q(self.internal_temp, self.external_temp)
        return Q_tot
    
    def cost(self):
        cost_tot = 0
        for appliance in self.appliances:
            cost_tot += appliance.cost
        for wall in self.surfaces:
            cost_tot += wall.total_cost()
        return cost_tot
    
    def EC(self):
        EC_tot = 0
        for appliance in self.appliances:
            EC_tot += appliance.EC
        for wall in self.surfaces:
            EC_tot += wall.total_EC()
        return EC_tot

    def operational_carbon(self): # returns kg/s
        P_gas_tot = 0
        for appliance in self.appliances:
            if appliance.enabled:
                P_gas_tot += appliance.energy_consumption * appliance.fraction_gas
        return P_gas_tot / natural_gas_energy_density
    
    def total_appliance_power(self, behaviour=HEATER):
        Q_tot = 0
        for appliance in self.appliances:
            if appliance.enabled:
                Q_tot += appliance.energy_consumption * appliance.efficiency * appliance.behaviour
        return Q_tot

    def print_all(self):
        print("=== House Geometry ===")
        print("Volume:", round(house.volume()), "m^3")
        print("Gross floor area:", house.gross_floor_area(), "m^2")

        print("\n=== Retrofits Information ===")
        print("Cost: ${:.2f}".format(house.cost()))
        cost_per_area = house.cost() / (house.gross_floor_area() * 10.764)
        print("Cost per Square Foot: ${:.2f}".format(cost_per_area))
        print("Embodied carbon:", round(house.EC()), "kgCO2e")
        print("Embodied carbon per Gross Floor Area:", round(house.EC() / house.gross_floor_area(), 2), "kgCO2e/m2")

        print("\n=== House Heating Systems Information === ")
        print("Operational carbon per month:", round(house.operational_carbon() * 86400 * 30), "kgCO2e")
        print("Maximum heating power:", round(house.total_appliance_power(HEATER)), "W")
        # print("Total cooling power:", house.total_appliance_power(AIR_CONDITIONER))
        print("Required heating power to maintain constant temperature (counteract envelope heat loss):", round(house.Q()), "W")
        

class Wall:
    def __init__(self, area, layers_thickness=[], layers_RSI=[], layers_density=[], layers_EC=[], layers_cost=[]):
        self.area = area
        self.layers_thickness = layers_thickness # Must be supplied in inches (matching RSI per inch)
        self.layers_RSI = layers_RSI
        self.layers_density = layers_density
        self.layers_EC = layers_EC
        self.layers_cost = layers_cost

    def total_thermal_resistance(self):
        total_RSI = 0
        for i in range(len(self.layers_RSI)):
            total_RSI += self.layers_RSI[i] * self.layers_thickness[i]
        return total_RSI

    def total_EC(self):
        total_EC = 0
        for i in range(len(self.layers_RSI)):
            mass = self.area * self.layers_thickness[i] * inches_to_meters * self.layers_density[i]
            total_EC += mass * self.layers_EC[i]
        return total_EC
    
    def total_cost(self):
        total_cost = 0
        for i in range(len(self.layers_RSI)):
            mass = self.area * self.layers_thickness[i] * inches_to_meters * self.layers_density[i]
            total_cost += mass * self.layers_cost[i]
        return total_cost

    def Q(self, T_in, T_out): # Assumes positive direction is going outwards
        total_RSI = self.total_thermal_resistance()
        return (T_in - T_out) * self.area / total_RSI


class Window:
    def __init__(self, area, RSI, EC, cost):
        self.area = area
        self.RSI = RSI
        self.EC = EC
        self.cost = cost
    
    def total_thermal_resistance(self):
        return self.RSI

    def total_EC(self):
        return self.EC
    
    def total_cost(self):
        return self.cost

    def Q(self, T_in, T_out): # Assumes positive direction is going outwards
        return (T_in - T_out) * self.area / self.RSI


class Appliance:
    def __init__(self, behaviour, efficiency, energy_consumption, fraction_gas, EC, cost, enabled=True):
        self.behaviour = behaviour # Defines direction by which it interacts with heat
        self.efficiency = efficiency # Percentage energy efficiency
        self.energy_consumption = energy_consumption # Watts
        self.fraction_gas = fraction_gas # Fraction of energy consumption supplied by gas rather than electricity
        self.EC = EC
        self.cost = cost
        self.enabled = enabled


print("\n==============================================================================================================================")
print("Sample 1950s house, No retrofits, Winter -- Data from EnerGuide homeowner information sheet")
print("==============================================================================================================================\n")

house = House(22, -6.7) # Inside temp, Outside temp
house.storeys = [(91.9, 2), (101.5, 2), (91.9, 1 * (1/2))]
#                 Basement   Main floor    Attic (~half height bc triangular roof)

# Walls -- 0 density (ignore), 0 EC, and $0 because no added retrofits yet
house.add_surface(
    Wall(30.8, [1], [0.82], [0], [0], [0]), # Brick/wood interior, 8 inches concrete block, estimate 11 inches total
    Wall(75, [1], [0.86], [0], [0], [0]), # 8 inches concrete block

    Wall(101.5, [1], [4.85], [0], [0], [0]), # Main roof (attic & gable), excluding porch

    Window(17.64, 0.3875, 0, 0), # No individual area data :. average RSI of all 8 windows, mostly double-paned

    Window(3.51, 0.39, 0, 0), # Solid wood door
    Window(3.51, 0.98, 0, 0), # Steel polystyrene door

    # Basement/Foundation
    Wall(44.5, [1], [1.75], [0], [0], [0]),
    Wall(4.4, [1], [0.8], [0], [0], [0]),
    Wall(5.5, [1], [2.79], [0], [0], [0]),
)

house.add_appliance(
    # Combi DHW heater :. Water heater same system as space heater
    # Uncomment one or the other depending on season:
    Appliance(HEATER, 0.95, 18000 / 0.95, 1, 0, 0, True), # Condensing 100% natural-gas space heater, 18 kW max output
    Appliance(AIR_CONDITIONER, 1, 32000 / 10, 0, 0, 0, False), # Central air conditioner
    # https://en.wikipedia.org/wiki/Seasonal_energy_efficiency_ratio
    # https://idesignac.com/blog/does-air-conditioning-use-gas-or-electricity/
)

house.print_all()

print("\n==============================================================================================================================")
print("Sample 1950s house, No retrofits, Summer -- Data from EnerGuide homeowner information sheet")
print("==============================================================================================================================\n")

house = House(22, 26.6) # Inside temp, Outside temp
house.storeys = [(91.9, 2), (101.5, 2), (91.9, 1 * (1/2))]
#                 Basement   Main floor    Attic (~half height bc triangular roof)

# Walls -- 0 density (ignore), 0 EC, and $0 because no added retrofits yet
house.add_surface(
    Wall(30.8, [1], [0.82], [0], [0], [0]), # Brick/wood interior, 8 inches concrete block, estimate 11 inches total
    Wall(75, [1], [0.86], [0], [0], [0]), # 8 inches concrete block

    Wall(101.5, [1], [4.85], [0], [0], [0]), # Main roof (attic & gable), excluding porch

    Window(17.64, 0.3875, 0, 0), # No individual area data :. average RSI of all 8 windows, mostly double-paned

    Window(3.51, 0.39, 0, 0), # Solid wood door
    Window(3.51, 0.98, 0, 0), # Steel polystyrene door

    # Basement/Foundation
    Wall(44.5, [1], [1.75], [0], [0], [0]),
    Wall(4.4, [1], [0.8], [0], [0], [0]),
    Wall(5.5, [1], [2.79], [0], [0], [0]),
)

house.add_appliance(
    # Combi DHW heater :. Water heater same system as space heater
    # Uncomment one or the other depending on season:
    Appliance(HEATER, 0.95, 18000 / 0.95, 1, 0, 0, False), # Condensing 100% natural-gas space heater, 18 kW max output
    Appliance(AIR_CONDITIONER, 1, 32000 / 10, 0, 0, 0, True), # Central air conditioner
    # https://en.wikipedia.org/wiki/Seasonal_energy_efficiency_ratio
    # https://idesignac.com/blog/does-air-conditioning-use-gas-or-electricity/
)

house.print_all()

print("\n==============================================================================================================================")
print("Same 1950s house, with proposed added retrofits, Winter")
print("==============================================================================================================================\n")

house = House(22, -6.7) # Inside temp, Outside temp
house.storeys = [(91.9, 2), (101.5, 2), (91.9, 1 * (1/2))]
#                 Basement   Main floor    Attic (~half height bc triangular roof)

# Reused data
layers_thickness = (1, 8)
layers_density = (0, 80)
layers_EC = (0, 0.144)
layers_cost = (0, 1.45)

house.add_surface(
    # Everything with added 8 inches loose cellulose fibre insulation
    # Density: 80 kg/m3 -- https://www.sciencedirect.com/science/article/pii/B9780081009826000057?via%3Dihub
    # Cost: $1.45/kg -- https://www.homedepot.ca/product/weathershield-cellulose-fiber-blowing-insulation-25-lbs-/1000167316
    Wall(30.8, layers_thickness, [0.82, 0.598], layers_density, layers_EC, layers_cost),
    Wall(75, layers_thickness, [0.86, 0.598], layers_density, layers_EC, layers_cost),

    Wall(101.5, layers_thickness, [4.85, 0.598], layers_density, layers_EC, layers_cost),

    Window(17.64, 1.149, 0, 0), # Triple-layered, annealed, copper-oxide coating (Low E), wood frame window

    # Doors remain unchanged -- beyond scope
    Window(3.51, 0.39, 0, 0), # Solid wood door
    Window(3.51, 0.98, 0, 0), # Steel polystyrene door

    # Basement/Foundation
    Wall(44.5, layers_thickness, [1.75, 0.598], layers_density, layers_EC, layers_cost),
    Wall(4.4, layers_thickness, [0.8, 0.598], layers_density, layers_EC, layers_cost),
    Wall(5.5, layers_thickness, [2.79, 0.598], layers_density, layers_EC, layers_cost),
)

ac_eff = 1 / (15.5 * 0.29307107)
house.add_appliance(
    # Assume same energy output, 95% efficiency during summer but 19% during winter -- https://www.nrel.gov/docs/fy16osti/65187.pdf
    Appliance(HEATER, 0.19, 18000 / 0.19, 0, 0, 9000, True), # Condensing 100% natural-gas space heater, 18 kW max output
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, False), # Data from https://www.lg.com/us/air-conditioners/lg-lw6023ivsm
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, False), # Data from https://www.lg.com/us/air-conditioners/lg-lw6023ivsm
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, False), # Data from https://www.lg.com/us/air-conditioners/lg-lw6023ivsm
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, False), # Data from https://www.lg.com/us/air-conditioners/lg-lw6023ivsm
    # Efficiency = 1 / CEER converted to Watts/Watts
    # Assume 4 rooms with AC
)

house.print_all()

print("\n==============================================================================================================================")
print("Same 1950s house, with proposed added retrofits, Summer")
print("==============================================================================================================================\n")

house = House(22, 26.6) # Inside temp, Outside temp
house.storeys = [(91.9, 2), (101.5, 2), (91.9, 1 * (1/2))]
#                 Basement   Main floor    Attic (~half height bc triangular roof)

# Reused data
layers_thickness = (1, 8)
layers_density = (0, 80)
layers_EC = (0, 0.144)
layers_cost = (0, 1.45)

house.add_surface(
    # Everything with added 8 inches loose cellulose fibre insulation
    # Density: 80 kg/m3 -- https://www.sciencedirect.com/science/article/pii/B9780081009826000057?via%3Dihub
    # Cost: $1.45/kg -- https://www.homedepot.ca/product/weathershield-cellulose-fiber-blowing-insulation-25-lbs-/1000167316
    Wall(30.8, layers_thickness, [0.82, 0.598], layers_density, layers_EC, layers_cost),
    Wall(75, layers_thickness, [0.86, 0.598], layers_density, layers_EC, layers_cost),

    Wall(101.5, layers_thickness, [4.85, 0.598], layers_density, layers_EC, layers_cost),

    Window(17.64, 1.149, 0, 0), # Triple-layered, annealed, copper-oxide coating (Low E), wood frame window

    # Doors remain unchanged -- beyond scope
    Window(3.51, 0.39, 0, 0), # Solid wood door
    Window(3.51, 0.98, 0, 0), # Steel polystyrene door

    # Basement/Foundation
    Wall(44.5, layers_thickness, [1.75, 0.598], layers_density, layers_EC, layers_cost),
    Wall(4.4, layers_thickness, [0.8, 0.598], layers_density, layers_EC, layers_cost),
    Wall(5.5, layers_thickness, [2.79, 0.598], layers_density, layers_EC, layers_cost),
)

ac_eff = 1 / (15.5 * 0.29307107)
house.add_appliance(
    # Assume same energy output, 95% efficiency during summer but 19% during winter -- https://www.nrel.gov/docs/fy16osti/65187.pdf
    Appliance(HEATER, 0.19, 18000 / 0.19, 0, 0, 9000, False), # Condensing 100% natural-gas space heater, 18 kW max output
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, True), # Data from https://www.lg.com/us/air-conditioners/lg-lw6023ivsm
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, True),
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, True),
    Appliance(AIR_CONDITIONER, ac_eff, 1758.42642 / ac_eff, 0, 0, 369, True),
    # Efficiency = 1 / CEER converted to Watts/Watts
    # Assume 4 rooms with AC
)

house.print_all()