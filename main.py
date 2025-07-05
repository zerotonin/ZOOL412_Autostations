# main.py
from sqlalchemy.orm import Session

from db.base import Base, engine
from db.models.inventory import Inventory
from db.models.user import User
from db.models.order import Order
from db.models.experiment import Experiment
from db.models.item_catalog import ItemCatalog
from db.models.geneweaver_experiment import GeneWeaverExperiment
from db.models.geneweaver_group import GeneWeaverGroup
from db.models.order import ArticleEnum
from db.models.acquisition import AcquisitionType
from db.models.hunting import AnimalSpecies


from db.user_experiments import UserExperiments
from db.user_actions import UserActions
from db.admin_actions import AdminActions


def test_geneweaver_dge():
    with Session(engine) as session:
        form_data = {
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
    test_hunting(AnimalSpecies.U51_M)
    test_hunting(AnimalSpecies.U51)
    test_order()
    test_advance_one_week()
    test_geneweaver_dge()
    test_geneweaver_viral()