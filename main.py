# main.py

# Base imports for SQLite and SQLAlchemy
from sqlalchemy.orm import Session
from db.base import Base, engine
# Import all models associated with purchasing, inventory, and users
from db.models.inventory import Inventory
from db.models.user import User
from db.models.order import Order
from db.models.item_catalog import ItemCatalog
from db.models.order import ArticleEnum
from db.models.acquisition import AcquisitionType
from db.models.hunting import AnimalSpecies
# Import all models associated with experiments
from db.models.experiment import Experiment
from db.models.geneweaver_experiment import GeneWeaverExperiment
from db.models.geneweaver_group import GeneWeaverGroup
from db.models.intraspectra_experiment import IntraspectraExperiment
from db.models.neurocartographer_experiment import NeuroCartographerExperiment
from db.models.panopticam_experiment import PanopticamExperiment, PanopticamGroup, PanopticamEvent, PanopticamPhase,PanopticamContingency
from db.models.polykiln_experiment import PolykilnExperiment
# Import all user actions and admin actions
from db.user_experiments import UserExperiments
from db.user_actions import UserActions
from db.admin_actions import AdminActions


def test_geneweaver_dge():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6", 
            "fold_change_threshold": 2,
            "max_sequences": 5000,
            "cell_type_level": "subtype",
            "cell_type_description": "Retinal ganglion cells",
            "groups": [
                {
                    "group_name": "Control",
                    "subject_ids": "A01, A02, A03, A04, A05",
                    "subject_count": 5,
                    "sampling_instructions": "Collect hippocampus tissue 30 min post-light."
                },
                {
                    "group_name": "Treatment",
                    "subject_ids": "A06, A07, A08, A09, A10",
                    "subject_count": 5,
                    "sampling_instructions": "Same as control + expose to drug X."
                }
            ]
        }

        UserExperiments.run_geneweaver_dge_analysis(
            user_id=1,
            form_data=form_data,
            session=session
        )

def test_geneweaver_viral():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6", 
            "gene_of_interest": "Knock out gene X for metabolic inhibition.",
            "promoter_sequence": "Only express under high calcium concentration.",
            "transduction_level": "subtype",
            "transduction_description": "Retinal ganglion cells",
            "groups": [
                {
                    "group_name": "Control_Vector",
                    "subject_count": 3,
                    "modification_type": "None",
                },
                {
                    "group_name": "Knockout_Group",
                    "subject_count": 5,
                    "modification_type": "Knockout",
                }
            ]
        }

        UserExperiments.run_geneweaver_viral_modification(
            user_id=1,
            form_data=form_data,
            session=session
        )


def initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")

def re_initialize_database():
    """Create tables in the SQLite database if they don't exist."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database initialized with all tables.")
    
def seed_initial_inventory():
    with Session(engine) as session:
        AdminActions.initialize_inventory(session)

def seed_test_users():
    with Session(engine) as session:
        AdminActions.create_test_users(session)

def seed_prices():
    with Session(engine) as session:
        AdminActions.initialize_item_catalog(session)

def test_order():
    with Session(engine) as session:
        order = UserActions.place_order(
            session=session,
            user_id=1,
            article=ArticleEnum.XATTY_CARTRIDGE,
            acquisition_type=AcquisitionType.QUICK,
        )
        print(f"Order placed: {order.article} for {order.value:.2f} chuan")


def test_juicing():
    """
    Simulates applying Juiz to a TA under valid conditions.
    This tests:
    - Juice availability
    - Risk tracking
    - Order logging
    """
    with Session(engine) as session:
        try:
            order = UserActions.administer_juiz(
                session=session,
                ta_field="ta_saltos_shifts",  # Can be switched to other TAs
                user_id=1,  # Assumes test user with ID=1 exists
            )
            print(f"[SUCCESS] Juicing applied. Logged as: {order.article}")
        except Exception as e:
            print(f"[ERROR] {e}")


def test_advance_one_week():
    with Session(engine) as session:
        AdminActions.advance_one_week(session)

def test_hunting(species):
    with Session(engine) as session:
        UserActions.collect_animals(user_id=1, species=species, session=session)

def test_intraspectra_visual():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6_m", 
            "subject_count": 4,
            "imaging_technique": "Microscopy",
            "capture_type": "Time_Series",
            "frame_capture_rate": 60.0,
            "spectral_filter": "Infrared_Thermal",
            "microscopy_technique": "Fluorescence",
            "magnification_level": "40x",
            "region_of_interest": "Midbrain dorsal view, dissected and stained"
        }

        UserExperiments.run_intraspectra_visual(
            user_id=1,
            form_data=form_data,
            session=session
        )
def test_intraspectra_rt():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6",
            "subject_count": 5,
            "target_substance": "BioFluid_Oxygenation",
            "target_is_custom": False,
            "volume_capture_type": "Static_Volume",
            "region_of_interest": "Thoracic Ganglion Cluster",
            "volume_capture_rate": 0.5,  # only needed for dynamic
            "number_of_volumes": 20
        }

        UserExperiments.run_intraspectra_rt(
            user_id=1,
            form_data=form_data,
            session=session
        )

def test_neurocartographer_trace():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6",
            "subject_count": 3,
            "seed_neuron_locator": "Primary motor neuron innervating Dorsal Wing Elevator.",
            "tracer_transport_type": "Retrograde",
            "max_neurons_to_map": 120,
            "pathway_search_algorithm": (
                "Follow strongest spike correlation at each synaptic depth up to 4 steps. "
                "Prioritize high signal-to-noise and least adaptation neurons."
            )
        }

        UserExperiments.run_neurocartographer_trace(
            user_id=1,
            form_data=form_data,
            session=session
        )

def test_panopticam_monitoring():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6",
            "experiment_run_id": "Run_2025_07_A",
            "probe_type_used": "pH",  # Try "None" to reduce shift cost
            "total_monitoring_hours": 2.0,  # Combined across phases

            "experimental_groups": [
                {
                    "group_name": "Control",
                    "subject_count": 4,
                },
                {
                    "group_name": "Stimulus_A",
                    "subject_count": 4,
                }
            ],

            "event_dictionary": [
                {
                    "event_name": "Foraging_Bout",
                    "definition_type": "Natural Language Description",
                    "operational_definition": "Subject enters zone B and maintains locomotion below 0.03 m/s for ≥5 seconds.",
                    "quantification_method": "Duration"
                },
                {
                    "event_name": "Tone_Response",
                    "definition_type": "Response Characterization Request",
                    "operational_definition": "Following Tone_A activation, analyze biopotential and video for 10s to extract salient deviation.",
                    "quantification_method": "Latency"
                }
            ],

            "phase_sequence": [
                {
                    "phase_name": "Baseline",
                    "phase_duration": "1 hour",
                    "monitor_events_active": ["Foraging_Bout"],

                    "contingency_rules": [
                        {
                            "trigger_event_name": "Foraging_Bout",
                            "applicable_groups": ["Stimulus_A"],
                            "action_command": "Activate('Actuator_ToneA', {Volume: 0.8, Duration: '1.5s'})"
                        }
                    ]
                },
                {
                    "phase_name": "Stimulus",
                    "phase_duration": "1 hour",
                    "monitor_events_active": ["Tone_Response"],

                    "contingency_rules": [
                        {
                            "trigger_event_name": "Tone_Response",
                            "action_command": "System_Command('End_Phase')"
                        }
                    ]
                }
            ]
        }

        UserExperiments.run_panopticam_monitoring(
            user_id=1,
            form_data=form_data,
            session=session
        )

def test_polykiln_fabrication():
    with Session(engine) as session:
        form_data = {
            "subject_species": "animals_51u6",
            "object_name": "ReactiveProbeHousing_V2",
            "functional_description": (
                "Design a protective housing for an internal probe system "
                "that maintains thermal stability and allows flexible movement. "
                "The device must include passive airflow and sensor mounts."
            ),
            "assessed_size_tier": "M",
            "assessed_mechanical_tier": 2,
            "assessed_electronic_tier": 2
        }

        UserExperiments.run_polykiln_fabrication(
            user_id=1,
            form_data=form_data,
            session=session
        )


if __name__ == "__main__":
    re_initialize_database()
    seed_initial_inventory() 
    seed_test_users()
    seed_prices()

    # test_order()
    # test_juicing()
    # test_advance_one_week()
    # test_juicing()
    # test_advance_one_week()
    # test_hunting(AnimalSpecies.U51_M)
    # test_hunting(AnimalSpecies.U51)
    # test_order()
    # test_geneweaver_dge()
    # test_advance_one_week()
    # test_intraspectra_visual()
    # test_intraspectra_rt()
    # test_geneweaver_viral()
    # test_neurocartographer_trace()
    # test_panopticam_monitoring()
    test_polykiln_fabrication()