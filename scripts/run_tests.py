#!/usr/bin/env python3
"""
Comprehensive test runner for Candlestick Nano trading bot
Provides different test categories and environments
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Test runner with different categories and environments"""
    
    def __init__(self):
        self.project_root = project_root
        self.tests_dir = self.project_root / "tests"
        
    def run_unit_tests(self, verbose=False):
        """Run unit tests only"""
        print("🧪 Running Unit Tests...")
        
        unit_test_files = [
            "test_trading_bot_core.py",
            "test_combined_daemon.py", 
            "test_entry_daemon.py",
            "test_exit_daemon.py",
            "test_exit_utils.py",
            "test_buy.py"
        ]
        
        cmd = [
            "python", "-m", "pytest",
            *[str(self.tests_dir / f) for f in unit_test_files],
            "--tb=short",
            "-x"  # Stop on first failure
        ]
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        # Set integration test environment
        env = os.environ.copy()
        env["RUN_INTEGRATION_TESTS"] = "1"
        
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir / "test_integration_api.py"),
            str(self.tests_dir / "test_integration_wallet.py"),
            str(self.tests_dir / "test_metis_integration.py"),
            "--tb=short",
            "-m", "integration"
        ]
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root, env=env)
    
    def run_e2e_tests(self, verbose=False):
        """Run end-to-end tests"""
        print("🎯 Running End-to-End Tests...")
        
        # Check if devnet environment is configured
        required_vars = ["QUICKNODE_ENDPOINT", "WALLET_ADDRESS", "WALLET_PRIVATE_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables for E2E tests: {missing_vars}")
            print("💡 Source config/.envrc or set environment variables")
            return subprocess.CompletedProcess(args=[], returncode=1)
        
        env = os.environ.copy()
        env["RUN_SLOW_TESTS"] = "1"
        
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir / "test_e2e_trading_flow.py"),
            str(self.tests_dir / "test_end_to_end_devnet.py"),
            "--tb=short",
            "-m", "e2e"
        ]
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root, env=env)
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests"""
        print("⚡ Running Performance Tests...")
        
        env = os.environ.copy()
        env["RUN_PERFORMANCE_TESTS"] = "1"
        
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir / "test_performance.py"),
            "--tb=short",
            "-m", "performance"
        ]
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root, env=env)
    
    def run_env_tests(self, verbose=False):
        """Run environment and configuration tests"""
        print("🔧 Running Environment Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir / "test_env.py"),
            "--tb=short"
        ]
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_all_tests(self, verbose=False, include_slow=False):
        """Run all test categories"""
        print("🚀 Running All Tests...")
        
        env = os.environ.copy()
        env["RUN_INTEGRATION_TESTS"] = "1"
        env["RUN_PERFORMANCE_TESTS"] = "1"
        
        if include_slow:
            env["RUN_SLOW_TESTS"] = "1"
        
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "--tb=short"
        ]
        
        if not include_slow:
            cmd.extend(["-m", "not slow"])
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        return subprocess.run(cmd, cwd=self.project_root, env=env)
    
    def run_specific_test(self, test_file, test_name=None, verbose=False):
        """Run a specific test file or test function"""
        print(f"🎯 Running Specific Test: {test_file}")
        
        test_path = self.tests_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            return subprocess.CompletedProcess(args=[], returncode=1)
        
        cmd = ["python", "-m", "pytest", str(test_path)]
        
        if test_name:
            cmd.append(f"-k {test_name}")
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        # Set permissive environment for specific tests
        env = os.environ.copy()
        env["RUN_INTEGRATION_TESTS"] = "1"
        env["RUN_PERFORMANCE_TESTS"] = "1"
        env["RUN_SLOW_TESTS"] = "1"
        
        return subprocess.run(cmd, cwd=self.project_root, env=env)
    
    def check_dependencies(self):
        """Check if test dependencies are installed"""
        print("🔍 Checking Test Dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "requests",
            "solana",
            "solders",
            "base58",
            "aiohttp"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n💡 Install missing packages:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def generate_coverage_report(self, verbose=False):
        """Generate test coverage report"""
        print("📊 Generating Coverage Report...")
        
        try:
            import coverage
        except ImportError:
            print("❌ Coverage package not installed: pip install coverage")
            return subprocess.CompletedProcess(args=[], returncode=1)
        
        # Run tests with coverage
        cmd = [
            "python", "-m", "coverage", "run",
            "--source=src",
            "-m", "pytest",
            str(self.tests_dir),
            "-m", "not slow"  # Exclude slow tests for coverage
        ]
        
        env = os.environ.copy()
        env["RUN_INTEGRATION_TESTS"] = "1"
        
        result = subprocess.run(cmd, cwd=self.project_root, env=env)
        
        if result.returncode == 0:
            # Generate report
            subprocess.run(["python", "-m", "coverage", "report"], cwd=self.project_root)
            subprocess.run(["python", "-m", "coverage", "html"], cwd=self.project_root)
            print("📄 HTML coverage report generated in htmlcov/")
        
        return result

def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Candlestick Nano Test Runner")
    parser.add_argument("category", nargs="?", default="unit",
                      choices=["unit", "integration", "e2e", "performance", "env", "all", "coverage"],
                      help="Test category to run")
    parser.add_argument("--test-file", help="Specific test file to run")
    parser.add_argument("--test-name", help="Specific test function to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--include-slow", action="store_true", help="Include slow tests")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.check_deps:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)
    
    if args.test_file:
        result = runner.run_specific_test(args.test_file, args.test_name, args.verbose)
    elif args.category == "unit":
        result = runner.run_unit_tests(args.verbose)
    elif args.category == "integration":
        result = runner.run_integration_tests(args.verbose)
    elif args.category == "e2e":
        result = runner.run_e2e_tests(args.verbose)
    elif args.category == "performance":
        result = runner.run_performance_tests(args.verbose)
    elif args.category == "env":
        result = runner.run_env_tests(args.verbose)
    elif args.category == "coverage":
        result = runner.generate_coverage_report(args.verbose)
    elif args.category == "all":
        result = runner.run_all_tests(args.verbose, args.include_slow)
    
    print(f"\n{'✅ Tests Passed!' if result.returncode == 0 else '❌ Tests Failed!'}")
    sys.exit(result.returncode)

if __name__ == "__main__":
    main() 