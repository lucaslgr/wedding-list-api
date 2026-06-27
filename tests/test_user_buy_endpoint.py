import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("JWT_SECRET_KEY", "12345678901234567890123456789012")
os.environ.setdefault("USER_BUY_PASS_CODE", "test-user-buy-pass-code")

TEST_USER_BUY_PASS_CODE = os.environ["USER_BUY_PASS_CODE"]

from domain.models import Item
from infra.database import Base, get_db
from main import app


class UserBuyEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = f"{cls.temp_dir.name}/test_wedding_list.db"
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
        cls.temp_dir.cleanup()

    def setUp(self) -> None:
        with self.SessionLocal() as db:
            db.query(Item).delete()
            db.commit()

    def test_user_buy_success(self) -> None:
        item_id = self._create_item()

        response = self.client.patch(
            f"/items/{item_id}/buy/user",
            json={"is_bought": True, "pass_code": TEST_USER_BUY_PASS_CODE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_bought"])

    def test_user_buy_wrong_pass_code_forbidden(self) -> None:
        item_id = self._create_item()

        response = self.client.patch(
            f"/items/{item_id}/buy/user",
            json={"is_bought": True, "pass_code": "wrong"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Forbidden")

        with self.SessionLocal() as db:
            item = db.get(Item, item_id)
            self.assertIsNotNone(item)
            self.assertFalse(item.is_bought)

    def test_user_buy_missing_item(self) -> None:
        response = self.client.patch(
            "/items/999999/buy/user",
            json={"is_bought": True, "pass_code": TEST_USER_BUY_PASS_CODE},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Item not found")

    def test_user_buy_missing_pass_code_validation_error(self) -> None:
        item_id = self._create_item()

        response = self.client.patch(
            f"/items/{item_id}/buy/user",
            json={"is_bought": True},
        )

        self.assertEqual(response.status_code, 422)

    def _create_item(self) -> int:
        with self.SessionLocal() as db:
            item = Item(
                name="Plate Set",
                description="Elegant dishware",
                category="Kitchen",
                link1_url="https://example.com/plate-set",
                link1_label="Store",
                is_bought=False,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item.id


if __name__ == "__main__":
    unittest.main()