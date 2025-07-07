# File: db/user_experiments.py

# Calculation imports
from datetime import date, datetime
import math
# Base imports for SQLite and SQLAlchemy
from sqlalchemy.orm import Session
from db.models.inventory import Inventory
from db.models.order import ArticleEnum
# Specific imports for experiments
from db.models.experiment import Experiment
from db.models.geneweaver_experiment import GeneWeaverExperiment
from db.models.geneweaver_group import GeneWeaverGroup
from db.models.intraspectra_experiment import IntraspectraExperiment
from db.models.neurocartographer_experiment import NeuroCartographerExperiment
from db.models.panopticam_experiment import PanopticamExperiment, PanopticamGroup, PanopticamEvent, PanopticamPhase,PanopticamContingency
from db.models.polykiln_experiment import PolykilnExperiment
from db.models.virgo_experiment import VirgoExperiment
from db.models.item_catalog import ItemCatalog





class UserExperiments:

    # Static sub-routines for user experiment functions
    @staticmethod
    def check_ta_shifts_required(inventory: Inventory, required: int) -> bool:
        total = sum(
            getattr(inventory, f)
            for f in [
                "ta_saltos_shifts",
                "ta_nitro_shifts",
                "ta_helene_shifts",
                "ta_carnival_shifts",
            ]
        )
        return total >= required

    @staticmethod
    def deduct_ta_shifts(inventory: Inventory, required: int) -> None:
        remaining = required
        for field in [
            "ta_saltos_shifts",
            "ta_nitro_shifts",
            "ta_helene_shifts",
            "ta_carnival_shifts",
        ]:
            available = getattr(inventory, field)
            used = min(available, remaining)
            setattr(inventory, field, available - used)
            remaining -= used
            if remaining <= 0:
                break

    @staticmethod
    def check_animal_required(inventory: Inventory, species: str, shifts_required: float) -> bool:
        """
        Checks whether enough animal availability (in FTEs) exists for a given species.
        
        Each animal provides 30 shifts (1.0 FTE). This function converts required shifts
        into FTEs, then checks whether the inventory has enough available.

        Parameters
        ----------
        inventory : Inventory
            The current inventory instance from the database.
        species : str
            The target species, matching the inventory field naming scheme.
        shifts_required : float
            Total number of shifts needed in this experiment.

        Returns
        -------
        bool
            True if sufficient animal FTEs exist; False otherwise.
        """
        field = f"{species}_available"
        if not hasattr(inventory, field):
            print(f"[❌] Invalid species field: '{field}' not found in Inventory.")
            return False

        available = getattr(inventory, field)
        required_fte = shifts_required / 30.0

        if available >= required_fte:
            return True

        print(
            f"[❌] Not enough animals for species '{species}': "
            f"need {required_fte:.2f} FTE, have {available:.2f} FTE"
        )
        return False


    @staticmethod
    def deduct_animals(inventory: Inventory, species: str, shifts_required: float) -> None:
        """
        Deducts animal usage in FTEs from inventory based on the number of shifts used.

        Parameters
        ----------
        inventory : Inventory
            The current inventory instance from the database.
        species : str
            The target species for deduction.
        shifts_required : float
            The number of shifts the animals contributed.
        """
        field = f"{species}_available"
        if not hasattr(inventory, field):
            raise ValueError(f"Invalid species field: '{field}'")

        current = getattr(inventory, field)
        used_fte = shifts_required / 30.0
        setattr(inventory, field, current - used_fte)

        print(f"[✔] Deducted {used_fte:.2f} FTE from {species}. Remaining: {current - used_fte:.2f}")

    @staticmethod
    def deduct_credits(inventory: Inventory, amount: float) -> bool:
        if inventory.credits < amount:
            return False
        inventory.credits -= amount
        return True

    @staticmethod
    def calculate_ocs_cost(session: Session, unit_count: int, units_per_job: int = 1000) -> tuple[int, int]:
        """
        Calculates the number of OCS jobs and total cost using the item catalog.

        Parameters
        ----------
        session : Session
            SQLAlchemy session.
        unit_count : int
            Number of units (samples, frames, volumes) to process.
        units_per_job : int
            Number of units per job (default: 1000 for visual data, 50 for DGE).

        Returns
        -------
        tuple[int, int]
            (job_count, total_cost)
        """
        jobs = math.ceil(unit_count / units_per_job)

        item = session.query(ItemCatalog).filter_by(
            item_key=ArticleEnum.KPI_OCS_JOB.value
        ).first()

        if item is None:
            raise RuntimeError("KPI_OCS_JOB not found in ItemCatalog.")

        return jobs, jobs * int(item.chuan_cost)

    @staticmethod
    def get_inventory(session: Session) -> Inventory:
        """
        Retrieves the singleton Inventory object from the database.
        Raises an error if not initialized.
        """
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")
        return inventory

    @staticmethod
    def log_experiment(session: Session, user_id: int, subject_species: str,
                       autostation_name: str, experiment_type: str,
                       wait_weeks: int = 1) -> Experiment:
        """
        Creates and logs a new Experiment in the database.

        Parameters
        ----------
        session : Session
            SQLAlchemy session object.
        user_id : int
            ID of the user submitting the experiment.
        species : str
            Species the experiment is run on (e.g., 'animals_51u6').
        autostation : str
            The name of the autostation used.
        experiment_type : str
            The mode of the experiment (e.g., 'DGE Analysis').
        wait_weeks : int, optional
            Number of weeks until experiment result is ready.

        Returns
        -------
        Experiment
            The created and flushed experiment object.
        """
        
        exp = Experiment(
            user_id=user_id,
            autostation_name=autostation_name,
            experiment_type=experiment_type,
            subject_species=subject_species,
            date=date.today(),
            time=datetime.now().time(),
            wait_weeks=wait_weeks,
            is_complete=False,
        )
        session.add(exp)
        session.flush()
        return exp



    # Experiment functions

    @staticmethod
    def run_geneweaver_dge_analysis(user_id: int, form_data: dict, session: Session) -> None:
        """
        Run a DGE Analysis on the GeneWeaver autostation.
        Compute cost is handled via KPI Orbital Compute Suite (OCS).
        """
        inventory = UserExperiments.get_inventory(session)

        species = form_data["subject_species"]
        groups = form_data["groups"]
        total_samples = sum(g["subject_count"] for g in groups)
        shifts_required = math.ceil(total_samples / 5)
        max_sequences = form_data["max_sequences"]
        fold_threshold = form_data["fold_change_threshold"]
        animal_shifts =shifts_required*total_samples

        # 🧪 Cartridge check
        if inventory.xatty_cartridge < 1:
            print("[❌] Not enough XATTY cartridges available.")
            return

        # 🧠 TA shifts check
        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return

        # 🧮 OCS jobs = ceil((samples × max_sequences) / 20)
        ocs_units = (
            total_samples * max_sequences
            if max_sequences > 0
            else total_samples * 1000
        )
        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=ocs_units,
            units_per_job=100
        )

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS jobs: need {ocs_cost}, have {inventory.credits}.")
            return

        # ✅ Dry Run Output
        print("\n[💡] GeneWeaver DGE Analysis — Dry Run")
        print("=====================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"🔬 Samples:             {total_samples}")
        print(f"📉 Fold Change Cutoff:  {fold_threshold}")
        print(f"📊 Max Sequences:       {max_sequences}")
        print(f"🧠 TA Shifts Required:  {shifts_required}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"🧪 Cartridge Required:  1 XATTY")
        print(f"🖥️ OCS Units:           {ocs_units}")
        print(f"🖥️ OCS Jobs:            {ocs_jobs}")
        print(f"💴 OCS Compute Cost:    {ocs_cost} chuan")
        print("=====================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.xatty_cartridge -= 1
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)
        inventory.credits -= ocs_cost

        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="GeneWeaver",
            experiment_type="DGE Analysis",
            subject_species=species,  
            wait_weeks=2
        )

        gexp = GeneWeaverExperiment(
            experiment_id=exp.id,
            mode="DGE",
            fold_change_threshold=fold_threshold,
            max_sequences=max_sequences,
            cell_type_level=form_data["cell_type_level"],
            cell_type_description=form_data["cell_type_description"],
            cartridge_used=ArticleEnum.XATTY_CARTRIDGE.value,
        )
        session.add(gexp)
        session.flush()

        for group in groups:
            group_entry = GeneWeaverGroup(
                geneweaver_experiment_id=gexp.id,
                group_name=group["group_name"],
                subject_count=group["subject_count"],
                sampling_instructions=group["sampling_instructions"],
            )
            session.add(group_entry)

        session.commit()
        print(f"[✔] GeneWeaver DGE experiment booked. Total cost: {ocs_cost} chuan.")

    


    @staticmethod
    def run_geneweaver_viral_modification(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a Viral Vector Gene Modification experiment on the GeneWeaver Autostation.
        Validates and deducts resources before creating experiment and group entries.
        """
        inventory = UserExperiments.get_inventory(session)


        species = form_data["subject_species"]
        groups = form_data["groups"]
        total_animals = sum(g["subject_count"] for g in groups)
        shifts_required = total_animals
        cartridge_field = "xatty_cartridge"
        animal_shifts =shifts_required*total_animals

        # 🐁 Animal availability check
        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return

        # Resource checks
        if inventory.xatty_cartridge < 1:
            print("[❌] Not enough XATTY cartridges available.")
            return

        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return


        print("\n[💡] GeneWeaver Viral Vector Modification — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"🐁 Subjects:            {total_animals}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"🧪 Cartridge Required:  1 XATTY")
        print("💾 Compute Units:       0")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.xatty_cartridge -= 1

        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)


        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="GeneWeaver",
            experiment_type="Viral Vector Modification",
            subject_species=species,  
            wait_weeks=3,
        )

        gexp = GeneWeaverExperiment(
            experiment_id=exp.id,
            mode="Viral",
            gene_of_interest=form_data["gene_of_interest"],
            promoter_sequence=form_data.get("promoter_sequence"),
            transduction_level=form_data["transduction_level"],
            transduction_description=form_data["transduction_description"],
            cartridge_used=ArticleEnum.XATTY_CARTRIDGE.value,
        )
        session.add(gexp)
        session.flush()

        for group in groups:
            group_entry = GeneWeaverGroup(
                geneweaver_experiment_id=gexp.id,
                group_name=group["group_name"],
                subject_count=group["subject_count"],
                modification_type=group["modification_type"]
            )
            session.add(group_entry)

        session.commit()
        print(f"[✔] Viral Vector Modification experiment booked for user {user_id}.")


    @staticmethod
    def run_intraspectra_visual(user_id: int, form_data: dict, session: Session) -> None:
        """
        Run a Visual Data Acquisition experiment on the Intraspectra Iris Mark II.
        Validates resources and calculates OCS cost. Asks user confirmation.
        """
        inventory = UserExperiments.get_inventory(session)

        # Inputs
        species = form_data["subject_species"]
        subject_count = form_data["subject_count"]
        capture_type = form_data["capture_type"]
        frame_rate = form_data.get("frame_capture_rate", None)
        imaging_mode = form_data["imaging_technique"]

        # Compute shifts required
        if capture_type == "Single_Frame":
            samples_per_shift = 3
        elif capture_type == "Time_Series":
            samples_per_shift = 5
        else:
            raise ValueError("Invalid capture type.")


        # Estimate frames per subject
        total_frames = (
            subject_count*3 if capture_type == "Single_Frame"
            else subject_count * 10# max for time series (adjust if dynamic input)
        )
        shifts_required = math.ceil(total_frames / samples_per_shift)
        animal_shifts =shifts_required
        
        # Compute OCS jobs
        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=total_frames,
            units_per_job=2  # 1000 frames per job
        )

        # 🧪 Cartridge check
        if inventory.zeropoint_cartridge < 1:
            print("[❌] Not enough ZeroPoint cartridges available.")
            return

        # 🐁 Animal availability check
        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return

        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return


        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS compute (need {ocs_cost}, have {inventory.credits}).")
            return

        print("\n[💡] Intraspectra Visual Acquisition — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"📸 Subjects:            {subject_count}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"🧪 Cartridge Required:  1 ZeroPoint")
        print(f"🖥️ OCS Jobs:            {ocs_jobs}")
        print(f"💴 OCS Compute Cost:    {ocs_cost} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct shifts
        inventory.zeropoint_cartridge -= 1
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)


        # Deduct credits
        inventory.credits -= ocs_cost

        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Intraspectra",
            experiment_type="Visual Acquisition",
            subject_species=species,  
            wait_weeks=1,
        )

        visual = IntraspectraExperiment(
            experiment_id=exp.id,
            mode="visual",
            subject_count=subject_count,
            region_of_interest=form_data["region_of_interest"],
            imaging_technique=form_data["imaging_technique"],
            capture_type=capture_type,
            spectral_filter=form_data.get("spectral_filter"),
            frame_capture_rate=frame_rate,
            microscopy_technique=form_data.get("microscopy_technique"),
            magnification_level=form_data.get("magnification_level"),
            cartridge_used=None
        )
        session.add(visual)
        session.commit()
        print(f"[✔] Intraspectra visual experiment booked successfully.")

    @staticmethod
    def run_intraspectra_rt(user_id: int, form_data: dict, session: Session) -> None:
        """
        Run a Resonance Tomography experiment on the Intraspectra Iris Mark II.
        Validates resources, handles ZeroPoint cartridge, calculates OCS cost.
        """
        inventory = UserExperiments.get_inventory(session)

        species = form_data["subject_species"]
        subject_count = form_data["subject_count"]
        volume_type = form_data["volume_capture_type"]  # "Static_Volume" or "Dynamic_Volume_Series"
        is_custom = form_data.get("target_is_custom", False)
        number_of_volumes = form_data.get("number_of_volumes", 1)

        # 🧮 Shifts required
        base_per_2_shifts = 10 if volume_type == "Static_Volume" else 5
        shifts_required = math.ceil(subject_count / base_per_2_shifts) * 2
        if is_custom:
            shifts_required += 2  # add +2 for custom targets

        animal_shifts = shifts_required * subject_count

        # 🧮 Volumes for OCS: assume 1 volume per subject if static, else subject * number_of_volumes
        total_volumes = (
            subject_count if volume_type == "Static_Volume"
            else subject_count * number_of_volumes
        )

        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=total_volumes,
            units_per_job=10
        )

        # 🧪 Cartridge check
        if inventory.zeropoint_cartridge < 1:
            print("[❌] Not enough ZeroPoint cartridges available.")
            return

        # 🐁 Animal availability
        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return

        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS compute (need {ocs_cost}, have {inventory.credits}).")
            return

        # ✅ Dry Run
        print("\n[💡] Intraspectra Resonance Tomography — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"📸 Subjects:            {subject_count}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"🧪 Cartridge Required:  1 ZeroPoint")
        print(f"🧠 OCS Units (Volumes): {total_volumes}")
        print(f"🖥️ OCS Jobs:            {ocs_jobs}")
        print(f"💴 OCS Compute Cost:    {ocs_cost} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.zeropoint_cartridge -= 1
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)
        inventory.credits -= ocs_cost

        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Intraspectra",
            experiment_type="Resonance Tomography",
            subject_species=species,
            wait_weeks=2
        )

        rt = IntraspectraExperiment(
            experiment_id=exp.id,
            mode="rt",
            subject_count=subject_count,
            region_of_interest=form_data["region_of_interest"],
            target_substance=form_data["target_substance"],
            target_is_custom=is_custom,
            volume_capture_type=volume_type,
            number_of_volumes=number_of_volumes,
            volume_capture_rate=form_data.get("volume_capture_rate"),
            cartridge_used=ArticleEnum.ZEROPOINT_CARTRIDGE.value
        )
        session.add(rt)
        session.commit()
        print(f"[✔] Intraspectra Resonance Tomography experiment booked successfully.")

    @staticmethod
    def run_neurocartographer_trace(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a Directed Circuit Trace experiment on the NeuroCartographer autostation.
        Deducts TA shifts, NC-PK1 cartridge, and OCS compute based on max neurons to trace.
        """
        inventory = UserExperiments.get_inventory(session)

        # Inputs
        species = form_data["subject_species"]
        subject_count = form_data["subject_count"]
        tracer_type = form_data["tracer_transport_type"]
        max_neurons = form_data["max_neurons_to_map"]

        # Shifts and FTE calculation
        shifts_required = 10 + subject_count + max_neurons * 2 # 10 base + 1 per subject + 2 per neuron 
        animal_shifts = shifts_required * subject_count - 10 # full burden model

        # Compute cost: ¥3 per neuron
        ocs_units = max_neurons
        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=ocs_units,
            units_per_job=1  # 1 neuron per unit
        )

        # Resource checks
        if inventory.nc_pk1_cartridge < 1:
            print("[❌] Not enough NC-PK1 cartridges available.")
            return

        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return

        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS compute (need {ocs_cost}, have {inventory.credits}).")
            return

        # ✅ Dry Run
        print("\n[💡] NeuroCartographer Circuit Trace — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:              {user_id}")
        print(f"🧠 Subjects:             {subject_count}")
        print(f"🧪 Shifts Required:      {shifts_required}")
        print(f"🐁 Animal FTE Required:  {(animal_shifts / 30):.2f}")
        print(f"💉 Cartridge Required:   1 NC-PK1")
        print(f"🧠 Neurons To Trace:     {max_neurons}")
        print(f"🖥️ OCS Jobs:             {ocs_jobs}")
        print(f"💴 OCS Compute Cost:     {ocs_cost} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.nc_pk1_cartridge -= 1
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)
        inventory.credits -= ocs_cost

        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="NeuroCartographer",
            experiment_type="Directed Circuit Trace",
            subject_species=species,
            wait_weeks=2,
        )

        trace = NeuroCartographerExperiment(
            experiment_id=exp.id,
            subject_count=subject_count,
            seed_neuron_locator=form_data["seed_neuron_locator"],
            tracer_transport_type=tracer_type,
            max_neurons_to_map=max_neurons,
            pathway_search_algorithm=form_data["pathway_search_algorithm"],
            cartridge_used=ArticleEnum.NC_PK1_CARTRIDGE.value
        )
        session.add(trace)
        session.commit()
        print(f"[✔] Directed Circuit Trace experiment booked successfully.")

    @staticmethod
    def run_panopticam_monitoring(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a Panopticam Behavioral Monitoring session.
        Handles group setup, event logging, phase structuring, contingency rules, and resource costs.
        """
        inventory = UserExperiments.get_inventory(session)

        species = form_data["subject_species"]
        total_subjects = sum(group["subject_count"] for group in form_data["experimental_groups"])
        probe_type = form_data.get("probe_type_used", "None")
        monitoring_hours = float(form_data["total_monitoring_hours"])
        event_count = len(form_data["event_dictionary"])
        phase_count = len(form_data["phase_sequence"])

        # Base shift cost
        subject_shift_cost = (0.5 if probe_type != "None" else 0.1)* total_subjects
        monitoring_shift_costs = total_subjects * monitoring_hours 
        shifts_required = subject_shift_cost + monitoring_shift_costs
        animal_shifts = shifts_required 
        # OCS Cost: 3 base + 1 per event + 0.5 per subject per hour
        ocs_jobs = monitoring_hours * total_subjects * event_count
        ocs_jobs, ocs_cost  = UserExperiments.calculate_ocs_cost(session,ocs_jobs, units_per_job=1)

        # Cartridge check
        if inventory.mamr_reel_cartrdige < 1:
            print("[❌] Not enough MAMR Reel cartridges available.")
            return

        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return

        if not UserExperiments.check_ta_shifts_required(inventory, math.ceil(shifts_required)):
            print("❌ Not enough TA shifts.")
            return

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS compute (need {ocs_cost}, have {inventory.credits}).")
            return

        # ✅ Dry Run Summary
        print("\n[💡] Panopticam Monitoring — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"🐁 Subjects:            {total_subjects}")
        print(f"🧠 Shifts Required:     {shifts_required:.2f}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"💉 Cartridge Required:  1 MAMR Reel")
        print(f"🧠 Events Defined:      {event_count}")
        print(f"⏱️ Duration (hrs):       {monitoring_hours}")
        print(f"💴 OCS Compute Cost:    {ocs_cost:.2f} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()
        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.mamr_reel_cartrdige -= 1
        UserExperiments.deduct_ta_shifts(inventory, math.ceil(shifts_required))
        UserExperiments.deduct_animals(inventory, species, animal_shifts)
        inventory.credits -= ocs_cost

        # Log Experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Panopticam",
            experiment_type="Define & Monitor Behavioral Events",
            subject_species=species,
            wait_weeks=2
        )

        pano = PanopticamExperiment(
            experiment_id=exp.id,
            experiment_run_id=form_data["experiment_run_id"],
            probe_type_used=probe_type,
            base_shift_cost=shifts_required,
            total_subjects=total_subjects,
            total_monitoring_hours=monitoring_hours,
            cartridge_used=ArticleEnum.MAMR_REEL_CARTRDIGE.value
        )
        session.add(pano)
        session.flush()

        # Add Groups
        for group in form_data["experimental_groups"]:
            session.add(PanopticamGroup(
                experiment_id=pano.id,
                group_name=group["group_name"],
                subject_count=group["subject_count"]
            ))

        # Add Events
        for event in form_data["event_dictionary"]:
            session.add(PanopticamEvent(
                experiment_id=pano.id,
                event_name=event["event_name"],
                definition_type=event["definition_type"],
                operational_definition=event["operational_definition"],
                quantification_method=event["quantification_method"]
            ))

        # Add Phases + Contingencies
        for phase in form_data["phase_sequence"]:
            phase_row = PanopticamPhase(
                experiment_id=pano.id,
                phase_name=phase["phase_name"],
                phase_duration=phase["phase_duration"],
                monitor_events_active=",".join(phase.get("monitor_events_active", []))
            )
            session.add(phase_row)
            session.flush()

            for rule in phase.get("contingency_rules", []):
                session.add(PanopticamContingency(
                    phase_id=phase_row.id,
                    trigger_event_name=rule["trigger_event_name"],
                    applicable_groups=",".join(rule.get("applicable_groups", [])) if rule.get("applicable_groups") else None,
                    action_command=rule["action_command"]
                ))

        session.commit()
        print("[✔] Panopticam monitoring session booked successfully.")


    @staticmethod
    def run_polykiln_fabrication(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a Polykiln Object Fabrication job.
        Determines workload, cartridge type, and OCS compute cost from complexity scores.
        """
        inventory = UserExperiments.get_inventory(session)

        # Extract parameters
        species = form_data["subject_species"]
        name = form_data["object_name"]
        description = form_data["functional_description"]
        size_tier = form_data["assessed_size_tier"]  # "S", "M", "L"
        mech_tier = int(form_data["assessed_mechanical_tier"])
        elec_tier = int(form_data["assessed_electronic_tier"])

        size_points = {"S": 1, "M": 2, "L": 3}[size_tier]
        score = (size_points * 2) + mech_tier + elec_tier

        # Determine cartridge
        if score <= 4:
            cartridge_field = "smart_filament_s_cartridge"
            cartridge_enum = ArticleEnum.SMART_FILAMENT_S_CARTRIDGE
            shift_cost = 1
            cartridge_name = "S"
        elif score <= 8:
            cartridge_field = "smart_filament_m_cartridge"
            cartridge_enum = ArticleEnum.SMART_FILAMENT_M_CARTRIDGE
            shift_cost = 3
            cartridge_name = "M"
        else:
            cartridge_field = "smart_filament_l_cartridge"
            cartridge_enum = ArticleEnum.SMART_FILAMENT_L_CARTRIDGE
            shift_cost = 5
            cartridge_name = "L"

        # Shift cost: 1 for S, 3 for M, 5 for L
        tier_shifts = [0, 1, 2, 3]  # Shifts for mech/elec tiers 0-3
        shifts_required = shift_cost + tier_shifts[mech_tier] + tier_shifts[elec_tier]

        # OCS Cost: Base 5 + mech tier + elec tier 
        tier_costs = [0, 1, 4, 9]  # Costs for mech/elec tiers 0-3
        ocs_level = 5 + tier_costs[mech_tier] + tier_costs[elec_tier]
        ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=ocs_level,
            units_per_job=10  # 1 chuan per unit
        )[1]


        # Validation
        if getattr(inventory, cartridge_field) < 1:
            print(f"[❌] Not enough {cartridge_name} Smart Filament cartridges.")
            return
    

        if not UserExperiments.check_ta_shifts_required(inventory, shift_cost):
            print("❌ Not enough TA shifts.")
            return

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits (need {ocs_cost}, have {inventory.credits}).")
            return

        # Summary
        print("\n[💡] Polykiln Fabrication — Dry Run")
        print("===================================================")
        print(f"🔧 Object:              {name}")
        print(f"📝 Description:         {description[:50]}...")
        print(f"📦 Size Tier:           {size_tier}")
        print(f"🧠 Shifts Required:     {shifts_required:.2f}")
        print(f"⚙️ Mechanical Tier:     {mech_tier}")
        print(f"🧠 Electronic Tier:     {elec_tier}")
        print(f"📈 Score:               {score}")
        print(f"📦 Cartridge Required:  {cartridge_name}")
        print(f"💾 OCS Compute Cost:    {ocs_cost} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this fabrication? [Y/n] ").strip().lower()
        if confirm != "" and confirm != "y":
            print("🚫 Fabrication not booked.")
            return

        # Deduct resources
        setattr(inventory, cartridge_field, getattr(inventory, cartridge_field) - 1)
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        inventory.credits -= ocs_cost

        # Log experiment
        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Polykiln",
            experiment_type="Object Fabrication",
            subject_species=species,
            wait_weeks=2,
        )

        job = PolykilnExperiment(
            experiment_id=exp.id,
            object_name=name,
            functional_description=description,
            size_tier=size_tier,
            mechanical_tier=mech_tier,
            electronic_tier=elec_tier,
            score=score,
            filament_type_used=cartridge_name,
            cartridge_used=cartridge_enum.value,
            shift_cost=shift_cost,
            ocs_compute_cost=ocs_cost
        )
        session.add(job)
        session.commit()
        print(f"[✔] Fabrication job for '{name}' booked successfully.")



    @staticmethod
    def run_virgo_analysis(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a compound analysis using the Virgo Flow Reactor.
        Handles new or known sample, optional Θ-OSP functional consultation.
        """
        inventory = UserExperiments.get_inventory(session)

        species = form_data["subject_species"]
        is_new_sample = bool(form_data.get("sample_source_description"))
        theta_requested = form_data.get("request_theta_analysis", False)

        shifts_required = 2 if is_new_sample else 1
        ocs_job = 1 if is_new_sample else 0.2
        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=ocs_job,
            units_per_job=1  # 1 chuan per job
        )
        if theta_requested:
            theta_cost = 8000
            ocs_cost += theta_cost

        animal_shifts = shifts_required if is_new_sample else 0

        if not UserExperiments.check_animal_required(inventory, species, animal_shifts):
            return
        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return
        if inventory.credits < ocs_cost:
            print(f"❌ Not enough credits (need {ocs_cost}, have {inventory.credits}).")
            return

        # Summary
        print("\n[💡] Virgo Analysis — Dry Run")
        print("======================================")
        print(f"📄 Reference: {form_data['analysis_reference_name']}")
        print(f"🧪 New Sample: {'Yes' if is_new_sample else 'No'}")
        print(f"🔍 Θ-OSP Consultation: {'Yes' if theta_requested else 'No'}")
        print(f"🧠 Shifts Required: {shifts_required}")
        print(f"🐁 Animal FTE Required: {(animal_shifts / 30):.2f}")
        print(f"💾 OCS Compute Cost: {ocs_cost} chuan including (Θ-OSP {theta_cost})")
        print("======================================")
        confirm = input("Proceed with analysis? [Y/n] ").strip().lower()
        if confirm != "" and confirm != "y":
            print("🚫 Analysis cancelled.")
            return

        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        UserExperiments.deduct_animals(inventory, species, animal_shifts)
        inventory.credits -= ocs_cost

        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Virgo",
            experiment_type="Compound Analysis",
            subject_species=species,
            wait_weeks=1
        )

        analysis = VirgoExperiment(
            experiment_id=exp.id,
            mode="analysis",
            sample_source_description=form_data.get("sample_source_description"),
            analysis_reference_name=form_data["analysis_reference_name"],
            request_theta_analysis=theta_requested,
            shifts_used=shifts_required,
            compute_cost=ocs_cost,
            cartridge_used=None
        )
        session.add(analysis)
        session.commit()
        print("[✔] Virgo compound analysis booked.")

    @staticmethod
    def run_virgo_synthesis(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a synthesis job using the Virgo Flow Reactor.
        Synthesizes known or novel compound (Θ-OSP request implied for novel).
        """
        inventory = UserExperiments.get_inventory(session)

        species = form_data["subject_species"]
        known = bool(form_data.get("target_compound_identifier"))
        is_novel = not known
        shifts_required = 3
        ocs_job = 1 if is_novel else 0

        ocs_jobs, ocs_cost = UserExperiments.calculate_ocs_cost(
            session=session,
            unit_count=ocs_job,
            units_per_job=1  # 1 chuan per job
        )

        cartridge_field = "dupont_cartridge"

        if getattr(inventory, cartridge_field) < 1:
            print("[❌] Not enough DuPont OmniChem Blue Capsules.")
            return
        
        if not UserExperiments.check_ta_shifts_required(inventory, shifts_required):
            print("❌ Not enough TA shifts.")
            return
        if inventory.credits < ocs_cost:
            print(f"❌ Not enough credits (need {ocs_cost}, have {inventory.credits}).")
            return

        # Summary
        print("\n[💡] Virgo Synthesis — Dry Run")
        print("======================================")
        print(f"🔬 Type: {'Novel (with Θ-OSP)' if is_novel else 'Known'}")
        print(f"🧠 Shifts Required: {shifts_required}")
        print(f"💊 Cartridge: DuPont OmniChem Blue Capsule")
        print(f"💾 OCS Compute Cost: {ocs_cost}")
        print("======================================")
        confirm = input("Proceed with synthesis? [Y/n] ").strip().lower()
        if confirm != "" and confirm != "y":
            print("🚫 Synthesis cancelled.")
            return

        inventory.dupont_cartridge -= 1
        UserExperiments.deduct_ta_shifts(inventory, shifts_required)
        inventory.credits -= ocs_cost

        exp = UserExperiments.log_experiment(
            session=session,
            user_id=user_id,
            autostation_name="Virgo",
            experiment_type="Synthesize Compound",
            subject_species=species,
            wait_weeks=2
        )

        synth = VirgoExperiment(
            experiment_id=exp.id,
            mode="synthesis",
            target_compound_identifier=form_data.get("target_compound_identifier"),
            desired_functional_effect=form_data.get("desired_functional_effect"),
            request_theta_analysis=is_novel,
            shifts_used=shifts_required,
            compute_cost=ocs_cost,
            cartridge_used=ArticleEnum.DUPONT_CARTRIDGE.value
        )
        session.add(synth)
        session.commit()
        print("[✔] Virgo synthesis job booked.")

