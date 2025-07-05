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


class UserExperiments:

    @staticmethod
    def run_geneweaver_dge_analysis(user_id: int, form_data: dict, session: Session) -> None:
        """
        Run a DGE Analysis on the GeneWeaver autostation. This version checks resource feasibility,
        prints a cost breakdown, and requests confirmation before committing.
        """
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        # Collect input
        groups = form_data["groups"]
        total_samples = sum(g["subject_count"] for g in groups)
        shifts_required = math.ceil(total_samples / 5)
        max_sequences = form_data["max_sequences"]
        fold_threshold = form_data["fold_change_threshold"]

        cartridge_field = "xatty_cartridge"
        if inventory.xatty_cartridge < 1:
            print("[❌] Not enough XATTY cartridges available.")
            return

        total_shifts_available = sum(
            getattr(inventory, field)
            for field in [
                "ta_saltos_shifts",
                "ta_nitro_shifts",
                "ta_helene_shifts",
                "ta_carnival_shifts",
            ]
        )
        if total_shifts_available < shifts_required:
            print(f"[❌] Not enough TA shifts (need {shifts_required}, have {total_shifts_available}).")
            return

        compute_cost = (
            total_samples * max_sequences
            if max_sequences > 0
            else total_samples * 1000  # conservative guess
        )

        print("\n[💡] GeneWeaver DGE Analysis — Dry Run")
        print("=====================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"🔬 Samples:             {total_samples}")
        print(f"📊 Max Sequences:       {max_sequences}")
        print(f"📉 Fold Change Cutoff:  {fold_threshold}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🧪 Cartridge Required:  1 XATTY")
        print(f"💾 Compute Units:       {compute_cost} chuan")
        print("=====================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct cartridge
        inventory.xatty_cartridge -= 1

        # Deduct shifts (greedy)
        remaining = shifts_required
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
            if remaining == 0:
                break

        # Deduct compute cost from credits
        if inventory.credits < compute_cost:
            print("[❌] Not enough credits available. Booking aborted.")
            return
        inventory.credits -= compute_cost

        # Log experiment
        exp = Experiment(
            user_id=user_id,
            autostation_name="GeneWeaver",
            experiment_type="DGE Analysis",
            date=date.today(),
            time=datetime.now().time(),
            wait_weeks=2,
            is_complete=False,
        )
        session.add(exp)
        session.flush()

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
        print(f"[✔] Experiment successfully booked.\n")



    @staticmethod
    def run_geneweaver_viral_modification(user_id: int, form_data: dict, session: Session) -> None:
        """
        Runs a Viral Vector Gene Modification experiment on the GeneWeaver Autostation.
        Validates and deducts resources before creating experiment and group entries.
        """
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        groups = form_data["groups"]
        total_animals = sum(g["subject_count"] for g in groups)
        shifts_required = total_animals
        cartridge_field = "xatty_cartridge"

        # Resource checks
        if inventory.xatty_cartridge < 1:
            print("[❌] Not enough XATTY cartridges available.")
            return

        total_shifts_available = sum(
            getattr(inventory, f)
            for f in [
                "ta_saltos_shifts",
                "ta_nitro_shifts",
                "ta_helene_shifts",
                "ta_carnival_shifts",
            ]
        )
        if total_shifts_available < shifts_required:
            print(f"[❌] Not enough TA shifts (need {shifts_required}, have {total_shifts_available}).")
            return

        print("\n[💡] GeneWeaver Viral Vector Modification — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"🐁 Subjects:            {total_animals}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🧪 Cartridge Required:  1 XATTY")
        print("💾 Compute Units:       0")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct resources
        inventory.xatty_cartridge -= 1

        remaining = shifts_required
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
            if remaining == 0:
                break

        # Log experiment
        exp = Experiment(
            user_id=user_id,
            autostation_name="GeneWeaver",
            experiment_type="Viral Vector Modification",
            date=date.today(),
            time=datetime.now().time(),
            wait_weeks=3,
            is_complete=False,
        )
        session.add(exp)
        session.flush()

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
        inventory = session.query(Inventory).first()
        if not inventory:
            raise RuntimeError("Inventory not initialized.")

        # Inputs
        subject_count = form_data["subject_count"]
        capture_type = form_data["capture_type"]
        frame_rate = form_data.get("frame_capture_rate", None)
        imaging_mode = form_data["imaging_technique"]

        # Compute shifts required
        if capture_type == "Single_Frame":
            samples_per_shift = 10
        elif capture_type == "Time_Series":
            samples_per_shift = 5
        else:
            raise ValueError("Invalid capture type.")

        shifts_required = math.ceil(subject_count / samples_per_shift)

        # Estimate frames per subject
        total_frames = (
            subject_count if capture_type == "Single_Frame"
            else subject_count * 10000  # max for time series (adjust if dynamic input)
        )

        # Compute OCS jobs
        ocs_jobs = math.ceil(total_frames / 1000)
        ocs_cost = ocs_jobs * 1000

        # Check TA shifts
        total_shifts_available = sum(
            getattr(inventory, f)
            for f in [
                "ta_saltos_shifts",
                "ta_nitro_shifts",
                "ta_helene_shifts",
                "ta_carnival_shifts",
            ]
        )
        if total_shifts_available < shifts_required:
            print(f"[❌] Not enough TA shifts (need {shifts_required}, have {total_shifts_available}).")
            return

        if inventory.credits < ocs_cost:
            print(f"[❌] Not enough credits for OCS compute (need {ocs_cost}, have {inventory.credits}).")
            return

        print("\n[💡] Intraspectra Visual Acquisition — Dry Run")
        print("===================================================")
        print(f"🧪 User ID:             {user_id}")
        print(f"📸 Subjects:            {subject_count}")
        print(f"🧠 Shifts Required:     {shifts_required}")
        print(f"🖥️ OCS Jobs:            {ocs_jobs}")
        print(f"💴 OCS Compute Cost:    {ocs_cost} chuan")
        print("===================================================")
        confirm = input("Proceed with booking this experiment? [Y/n] ").strip().lower()

        if confirm != "" and confirm != "y":
            print("🚫 Experiment not booked.")
            return

        # Deduct shifts
        remaining = shifts_required
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
            if remaining == 0:
                break

        # Deduct credits
        inventory.credits -= ocs_cost

        # Log experiment
        exp = Experiment(
            user_id=user_id,
            autostation_name="Intraspectra",
            experiment_type="Visual Acquisition",
            date=date.today(),
            time=datetime.now().time(),
            wait_weeks=1,
            is_complete=False,
        )
        session.add(exp)
        session.flush()

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