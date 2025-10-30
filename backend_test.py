#!/usr/bin/env python3
"""
VetMed Pro Backend Testing Suite
Comprehensive tests for veterinary consultation platform
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
import sys
import os

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test data for Mexican veterinary professionals (will be generated dynamically)
def generate_test_vet_data():
    unique_id = str(uuid.uuid4().int)[:8]  # Generate numeric unique ID
    return {
        "nombre": "Dr. María Elena Rodríguez Hernández",
        "email": f"maria.rodriguez.{unique_id}@veterinaria.mx",
        "telefono": "+52 55 1234 5678",
        "cedula_profesional": f"1234{unique_id}",  # Valid format for Mexican veterinary license (all digits, >6 chars)
        "especialidad": "Medicina Interna de Pequeñas Especies",
        "años_experiencia": 8,
        "institucion": "Universidad Nacional Autónoma de México (UNAM)"
    }

TEST_CONSULTATION_DATA = {
    "fecha": datetime.now().strftime("%Y-%m-%d"),
    "nombre_mascota": "Firulais",
    "nombre_dueño": "Juan Pérez",
    "raza": "Pastor Alemán",
    "edad": "5 años",
    "peso": "32 kg",
    "condicion_corporal": "NORMAL",
    "sexo": "MACHO",
    "estado_reproductivo": "ENTERO",
    "vacunas_vigentes": "SI",
    "detalle_paciente": (
        "Vómitos recurrentes y pérdida de apetito desde hace 3 días. "
        "Vómitos amarillentos, letargia, rechazo al alimento, deshidratación leve. "
        "Tratamientos previos: ayuno de 12 horas, suero oral."
    )
}

TEST_OBSERVATIONS = {
    "parametros_vitales": "FC: 110 lpm, FR: 28 rpm, T: 39.2°C, mucosas pálidas",
    "ambiente_manejo": "Perro doméstico, alimentación con croquetas premium, acceso a jardín",
    "laboratorio_estudios": "Pendientes: hemograma completo, química sanguínea",
    "notas_adicionales": "Propietario refiere que el perro comió algo en el parque hace 4 días"
}

class VetMedProTester:
    def __init__(self):
        self.session = None
        self.test_vet_id = None
        self.test_consultation_id = None
        self.test_session_id = None
        self.test_vet_data = generate_test_vet_data()  # Generate unique test data
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()

    def log_result(self, test_name, success, message="", error=None):
        """Log test result"""
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if error:
            print(f"   Error: {error}")
            self.results["errors"].append(f"{test_name}: {error}")
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
        print()

    async def test_health_check(self):
        """Test 1: Health Check - API connectivity via animal categories"""
        try:
            # Test API connectivity using a simple endpoint
            async with self.session.get(f"{API_BASE}/animal-categories") as response:
                if response.status == 200:
                    data = await response.json()
                    if "categories" in data:
                        self.log_result("Health Check", True, "Backend API is accessible and responding")
                        return True
                    else:
                        self.log_result("Health Check", False, f"Unexpected response: {data}")
                        return False
                else:
                    self.log_result("Health Check", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Health Check", False, error=str(e))
            return False

    async def test_veterinarian_registration(self):
        """Test 2: Veterinarian Registration with Mexican license"""
        try:
            async with self.session.post(
                f"{API_BASE}/auth/register",
                json=self.test_vet_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_vet_id = data.get("id")
                    # Don't compare cedula directly since it's hashed in storage
                    if self.test_vet_id and data.get("email") == self.test_vet_data["email"]:
                        self.log_result("Veterinarian Registration", True, 
                                      f"Registered vet ID: {self.test_vet_id}")
                        return True
                    else:
                        self.log_result("Veterinarian Registration", False, 
                                      f"Invalid response data: {data}")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Veterinarian Registration", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Veterinarian Registration", False, error=str(e))
            return False

    async def test_veterinarian_login(self):
        """Test 3: Veterinarian Login with registered credentials"""
        if not self.test_vet_id:
            self.log_result("Veterinarian Login", False, "No registered vet to test login")
            return False

        try:
            login_data = {
                "email": self.test_vet_data["email"],
                "cedula_profesional": self.test_vet_data["cedula_profesional"]
            }
            
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("id") == self.test_vet_id:
                        self.log_result("Veterinarian Login", True, "Login successful")
                        return True
                    else:
                        self.log_result("Veterinarian Login", False, 
                                      f"ID mismatch: expected {self.test_vet_id}, got {data.get('id')}")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Veterinarian Login", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Veterinarian Login", False, error=str(e))
            return False

    async def test_invalid_login(self):
        """Test 4: Invalid Login Attempts"""
        try:
            invalid_login = {
                "email": "invalid@email.com",
                "cedula_profesional": "000000"
            }
            
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=invalid_login,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 401:
                    self.log_result("Invalid Login Test", True, "Correctly rejected invalid credentials")
                    return True
                else:
                    self.log_result("Invalid Login Test", False, 
                                  f"Expected 401, got {response.status}")
                    return False
        except Exception as e:
            self.log_result("Invalid Login Test", False, error=str(e))
            return False

    async def test_animal_categories(self):
        """Test 5: Retrieve Animal Categories"""
        try:
            async with self.session.get(f"{API_BASE}/animal-categories") as response:
                if response.status == 200:
                    data = await response.json()
                    categories = data.get("categories", {})
                    expected_categories = ["caninos", "felinos", "aves", "reptiles", "exoticos"]
                    
                    if all(cat in categories for cat in expected_categories):
                        self.log_result("Animal Categories", True, 
                                      f"Retrieved {len(categories)} categories")
                        return True
                    else:
                        self.log_result("Animal Categories", False, 
                                      f"Missing categories. Got: {list(categories.keys())}")
                        return False
                else:
                    self.log_result("Animal Categories", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Animal Categories", False, error=str(e))
            return False

    async def test_membership_packages(self):
        """Test 6: Retrieve Membership Packages"""
        try:
            async with self.session.get(f"{API_BASE}/membership/packages") as response:
                if response.status == 200:
                    data = await response.json()
                    packages = data.get("packages", {})
                    expected_packages = ["basic", "professional", "premium"]
                    
                    if all(pkg in packages for pkg in expected_packages):
                        self.log_result("Membership Packages", True, 
                                      f"Retrieved {len(packages)} packages")
                        return True
                    else:
                        self.log_result("Membership Packages", False, 
                                      f"Missing packages. Got: {list(packages.keys())}")
                        return False
                else:
                    self.log_result("Membership Packages", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Membership Packages", False, error=str(e))
            return False

    async def test_create_checkout_session(self):
        """Test 7: Create Stripe Checkout Session"""
        if not os.getenv("STRIPE_API_KEY"):
            self.log_result("Stripe Checkout Session", True, "SKIPPED: STRIPE_API_KEY not set")
            return True
        try:
            checkout_data = {
                "package_id": "basic",
                "origin_url": BASE_URL
            }
            
            async with self.session.post(
                f"{API_BASE}/payments/checkout/session",
                json=checkout_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_session_id = data.get("session_id")
                    checkout_url = data.get("checkout_url")
                    
                    if self.test_session_id and checkout_url:
                        self.log_result("Stripe Checkout Session", True, 
                                      f"Session ID: {self.test_session_id}")
                        return True
                    else:
                        self.log_result("Stripe Checkout Session", False, 
                                      f"Missing session data: {data}")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Stripe Checkout Session", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Stripe Checkout Session", False, error=str(e))
            return False

    async def test_checkout_status(self):
        """Test 8: Check Payment Status"""
        if not os.getenv("STRIPE_API_KEY"):
            self.log_result("Payment Status Check", True, "SKIPPED: STRIPE_API_KEY not set")
            return True
        if not self.test_session_id:
            self.log_result("Payment Status Check", False, "No session ID to check")
            return False

        try:
            async with self.session.get(
                f"{API_BASE}/payments/checkout/status/{self.test_session_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status")
                    payment_status = data.get("payment_status")
                    
                    if status and payment_status:
                        self.log_result("Payment Status Check", True, 
                                      f"Status: {status}, Payment: {payment_status}")
                        return True
                    else:
                        self.log_result("Payment Status Check", False, 
                                      f"Missing status data: {data}")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Payment Status Check", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Payment Status Check", False, error=str(e))
            return False

    async def test_create_consultation(self):
        """Test 9: Create Consultation (requires membership - will test without)"""
        if not self.test_vet_id:
            self.log_result("Create Consultation", False, "No vet ID available")
            return False

        try:
            consultation_request = {
                "veterinarian_id": self.test_vet_id,
                "category": "caninos",
                "consultation_data": TEST_CONSULTATION_DATA
            }
            
            async with self.session.post(
                f"{API_BASE}/consultations",
                json=consultation_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_consultation_id = data.get("id")
                    self.log_result("Create Consultation", True, 
                                  f"Consultation ID: {self.test_consultation_id}")
                    return True
                elif response.status == 403:
                    # Expected - no membership
                    error_data = await response.json()
                    if "Membresía requerida" in error_data.get("detail", ""):
                        self.log_result("Create Consultation", True, 
                                      "Correctly requires membership")
                        return True
                    else:
                        self.log_result("Create Consultation", False, 
                                      f"Unexpected 403 error: {error_data}")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Create Consultation", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Create Consultation", False, error=str(e))
            return False

    async def test_consultation_history(self):
        """Test 10: Get Consultation History"""
        if not self.test_vet_id:
            self.log_result("Consultation History", False, "No vet ID available")
            return False

        try:
            async with self.session.get(
                f"{API_BASE}/consultations/{self.test_vet_id}/history"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    consultations = data.get("consultations", [])
                    self.log_result("Consultation History", True, 
                                  f"Retrieved {len(consultations)} consultations")
                    return True
                else:
                    error_data = await response.text()
                    self.log_result("Consultation History", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Consultation History", False, error=str(e))
            return False

    async def test_llm_integration_with_membership(self):
        """Test 11: LLM Integration with Claude 4 Sonnet (Full workflow test)"""
        try:
            # Import os at the beginning
            import os
            from datetime import datetime, timezone
            from motor.motor_asyncio import AsyncIOMotorClient
            
            if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
                self.log_result("LLM Integration", True, "SKIPPED: Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY set")
                return True
            if not self.test_vet_id:
                self.log_result("LLM Integration", False, "No vet ID available")
                return False

            # First, simulate membership activation by directly updating the vet
            # This simulates what would happen after a successful payment
            future_date = datetime.now(timezone.utc).replace(month=12, day=31, year=2025)
            membership_data = {
                "membership_type": "basic",
                "consultations_remaining": 10,
                "membership_expires": future_date.isoformat()
            }
            
            # We'll use MongoDB directly to simulate membership activation
            # In a real scenario, this would happen via Stripe webhook
            
            # Connect to MongoDB using the same settings as the backend
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "savant_vet_db")
            mongo_client = AsyncIOMotorClient(mongo_url)
            db = mongo_client[db_name]
            
            # Update veterinarian with membership
            update_result = await db.veterinarians.update_one(
                {"id": self.test_vet_id},
                {"$set": membership_data}
            )
            
            if update_result.matched_count == 0:
                self.log_result("LLM Integration", False, "Failed to update veterinarian membership")
                return False
            
            # Now create a consultation
            consultation_request = {
                "veterinarian_id": self.test_vet_id,
                "category": "pequeñas",
                "consultation_data": TEST_CONSULTATION_DATA
            }
            
            async with self.session.post(
                f"{API_BASE}/consultations",
                json=consultation_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    consultation_data = await response.json()
                    consultation_id = consultation_data.get("id")
                    
                    if consultation_id:
                        # Now test the LLM analysis
                        async with self.session.post(
                            f"{API_BASE}/consultations/{consultation_id}/analyze"
                        ) as analyze_response:
                            if analyze_response.status == 200:
                                analysis_data = await analyze_response.json()
                                if analysis_data.get("analysis") and "consultation_id" in analysis_data:
                                    self.log_result("LLM Integration", True, 
                                                  "Claude 4 Sonnet analysis completed successfully")
                                    return True
                                else:
                                    self.log_result("LLM Integration", False, 
                                                  f"Invalid analysis response: {analysis_data}")
                                    return False
                            else:
                                error_data = await analyze_response.text()
                                self.log_result("LLM Integration", False, 
                                              f"Analysis failed {analyze_response.status}: {error_data}")
                                return False
                    else:
                        self.log_result("LLM Integration", False, "No consultation ID returned")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("LLM Integration", False, 
                                  f"Consultation creation failed {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("LLM Integration", False, error=str(e))
            return False

    async def test_database_persistence(self):
        """Test 12: Database Persistence - Verify vet data is stored"""
        if not self.test_vet_id:
            self.log_result("Database Persistence", False, "No vet ID to verify")
            return False

        try:
            async with self.session.get(
                f"{API_BASE}/veterinarians/{self.test_vet_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Don't compare cedula directly since it's hashed - verify email and other fields
                    if (data.get("email") == self.test_vet_data["email"] and 
                        data.get("nombre") == self.test_vet_data["nombre"]):
                        self.log_result("Database Persistence", True, 
                                      "Veterinarian data correctly stored and retrieved")
                        return True
                    else:
                        self.log_result("Database Persistence", False, 
                                      "Data mismatch in stored veterinarian")
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Database Persistence", False, 
                                  f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_result("Database Persistence", False, error=str(e))
            return False

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("[TEST] VetMed Pro Backend Testing Suite")
        print("=" * 50)
        print(f"Testing against: {BASE_URL}")
        print()

        await self.setup()
        
        try:
            # Core functionality tests
            await self.test_health_check()
            await self.test_veterinarian_registration()
            await self.test_veterinarian_login()
            await self.test_invalid_login()
            await self.test_animal_categories()
            
            # Payment system tests
            await self.test_membership_packages()
            await self.test_create_checkout_session()
            await self.test_checkout_status()
            
            # Consultation system tests
            await self.test_create_consultation()
            await self.test_consultation_history()
            await self.test_llm_integration_with_membership()
            
            # Database tests
            await self.test_database_persistence()
            
        finally:
            await self.cleanup()

        # Print summary
        print("=" * 50)
        print("[SUMMARY] TEST SUMMARY")
        print(f"[PASS] Passed: {self.results['passed']}")
        print(f"[FAIL] Failed: {self.results['failed']}")
        print(f"[RATE] Success Rate: {(self.results['passed']/(self.results['passed']+self.results['failed'])*100):.1f}%")
        
        if self.results['errors']:
            print("\n[ERROR] ERRORS ENCOUNTERED:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        return self.results['failed'] == 0

async def main():
    """Main test runner"""
    tester = VetMedProTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[WARNING] Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())