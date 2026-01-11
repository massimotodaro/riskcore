#!/usr/bin/env python3
"""
RISKCORE Mock Data Generator
=============================
Generates realistic test data for a multi-manager hedge fund scenario.

Usage:
    python scripts/generate_mock_data.py [--clean] [--scale small|medium|large]

Scale options:
    small:  1 tenant, 5 PMs, 50 securities, 200 positions
    medium: 1 tenant, 10 PMs, 200 securities, 1000 positions (default)
    large:  1 tenant, 20 PMs, 500 securities, 5000 positions

Author: RISKCORE Team
Date: 2026-01-11
"""

import argparse
import random
import string
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
import hashlib
import json
import sys

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# ============================================
# CONFIGURATION
# ============================================

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

SCALES = {
    "small": {
        "num_pms": 5,
        "num_securities": 50,
        "positions_per_book": 40,
        "days_of_prices": 30,
        "days_of_history": 30,
    },
    "medium": {
        "num_pms": 10,
        "num_securities": 200,
        "positions_per_book": 100,
        "days_of_prices": 60,
        "days_of_history": 60,
    },
    "large": {
        "num_pms": 20,
        "num_securities": 500,
        "positions_per_book": 250,
        "days_of_prices": 90,
        "days_of_history": 90,
    },
}

# ============================================
# REALISTIC DATA POOLS
# ============================================

# Fake but realistic company names and tickers
COMPANIES = [
    ("ACME Corp", "ACME", "Technology"),
    ("BlueSky Holdings", "BSKY", "Technology"),
    ("CyberDyne Systems", "CDYN", "Technology"),
    ("DataFlow Inc", "DFLW", "Technology"),
    ("EagleTech", "EGTC", "Technology"),
    ("FusionWare", "FUSN", "Technology"),
    ("GlobalNet", "GNET", "Technology"),
    ("HyperScale", "HYSC", "Technology"),
    ("InnoSoft", "INSF", "Technology"),
    ("JetStream", "JSTR", "Technology"),
    ("KronosTech", "KRON", "Technology"),
    ("LightSpeed", "LSPD", "Technology"),
    ("MegaByte", "MBYT", "Technology"),
    ("NexGen", "NXGN", "Technology"),
    ("OmniCore", "OMCR", "Technology"),
    ("PrimeLogic", "PLOG", "Technology"),
    ("QuantumBit", "QBIT", "Technology"),
    ("RapidCloud", "RCLD", "Technology"),
    ("SynergyX", "SYGX", "Technology"),
    ("TechNova", "TNOV", "Technology"),
    ("UltraNet", "ULNT", "Technology"),
    ("VectorSys", "VCTR", "Technology"),
    ("WaveForm", "WFRM", "Technology"),
    ("XenonLabs", "XLAB", "Technology"),
    ("YieldMax", "YMAX", "Technology"),
    ("ZenithAI", "ZNAI", "Technology"),
    ("AlphaBank", "ALBK", "Financials"),
    ("BetaCapital", "BCAP", "Financials"),
    ("CrestFinance", "CRFN", "Financials"),
    ("DeltaInvest", "DINV", "Financials"),
    ("EquityFirst", "EQFR", "Financials"),
    ("FortuneTrust", "FTRS", "Financials"),
    ("GoldmanLite", "GLTE", "Financials"),
    ("HarborBank", "HRBK", "Financials"),
    ("IronVault", "IVLT", "Financials"),
    ("JupiterFin", "JFIN", "Financials"),
    ("AeroJet", "ARJT", "Industrials"),
    ("BuildMax", "BMAX", "Industrials"),
    ("CoreSteel", "CSTL", "Industrials"),
    ("DuraMach", "DRMC", "Industrials"),
    ("EngineWorks", "EWKS", "Industrials"),
    ("ForgeIndustry", "FORG", "Industrials"),
    ("GearCo", "GRCO", "Industrials"),
    ("HeavyLift", "HVLF", "Industrials"),
    ("MediCure", "MDCR", "Healthcare"),
    ("NeuroPharma", "NRPH", "Healthcare"),
    ("OncoBio", "ONBI", "Healthcare"),
    ("PharmaGen", "PGEN", "Healthcare"),
    ("QuickCare", "QCRE", "Healthcare"),
    ("RadiantHealth", "RDHL", "Healthcare"),
    ("StemCell Plus", "STCP", "Healthcare"),
    ("TherapyOne", "THON", "Healthcare"),
    ("EcoEnergy", "ECEN", "Energy"),
    ("FuelTech", "FLTC", "Energy"),
    ("GreenPower", "GRPW", "Energy"),
    ("HydroGen", "HYGN", "Energy"),
    ("IonEnergy", "IONE", "Energy"),
    ("JouleMax", "JMAX", "Energy"),
    ("RetailKing", "RTKN", "Consumer Discretionary"),
    ("ShopSmart", "SHSM", "Consumer Discretionary"),
    ("TrendStyle", "TRST", "Consumer Discretionary"),
    ("UrbanBuy", "URBY", "Consumer Discretionary"),
    ("ValueMart", "VLMT", "Consumer Staples"),
    ("WholeFoods Plus", "WFPL", "Consumer Staples"),
    ("FreshFarm", "FFRM", "Consumer Staples"),
    ("NutriLife", "NTLF", "Consumer Staples"),
    ("CommSat", "CSAT", "Communication Services"),
    ("DigiMedia", "DGMD", "Communication Services"),
    ("EchoNet", "ECNT", "Communication Services"),
    ("FiberLink", "FBLK", "Communication Services"),
    ("PropertyMax", "PMAX", "Real Estate"),
    ("RealtyTrust", "RLTT", "Real Estate"),
    ("UrbanSpace", "URSP", "Real Estate"),
    ("VentureREIT", "VRET", "Real Estate"),
    ("ChemWorks", "CHWK", "Materials"),
    ("MetalPrime", "MTPR", "Materials"),
    ("PolymerTech", "PLYT", "Materials"),
    ("RawMaterials Inc", "RWMT", "Materials"),
    ("CloudUtil", "CLUT", "Utilities"),
    ("PowerGrid", "PWGD", "Utilities"),
    ("WaterWorks", "WTWK", "Utilities"),
]

STRATEGIES = [
    "Long/Short Equity",
    "Event Driven",
    "Global Macro",
    "Quantitative",
    "Credit",
    "Convertible Arb",
    "Merger Arb",
    "Distressed",
    "Multi-Strategy",
    "Sector Specialist",
]

PM_FIRST_NAMES = [
    "James", "Michael", "David", "Robert", "William",
    "Sarah", "Jennifer", "Emily", "Jessica", "Amanda",
    "Christopher", "Matthew", "Daniel", "Andrew", "Joshua",
    "Elizabeth", "Michelle", "Stephanie", "Nicole", "Katherine",
]

PM_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Chen", "Wang", "Li", "Zhang", "Liu",
    "Patel", "Kim", "Singh", "Cohen", "Murphy",
]

COUNTRIES = ["USA", "GBR", "DEU", "FRA", "JPN", "CHN", "CAN", "AUS", "CHE", "SGP"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "SGD"]
EXCHANGES = ["NYSE", "NASDAQ", "LSE", "TSE", "XETRA", "HKEX", "SGX"]

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_figi():
    """Generate a fake but valid-format FIGI (12 chars, BBG + 8 alphanum + check)."""
    chars = string.ascii_uppercase + string.digits
    middle = ''.join(random.choices(chars, k=8))
    check = random.choice(string.digits)
    return f"BBG{middle}{check}"


def generate_cusip():
    """Generate a fake CUSIP (9 chars: 6 issuer + 2 issue + 1 check)."""
    chars = string.ascii_uppercase + string.digits
    issuer = ''.join(random.choices(chars, k=6))
    issue = ''.join(random.choices(string.digits, k=2))
    check = random.choice(string.digits)
    return f"{issuer}{issue}{check}"


def generate_isin(country="US", cusip=None):
    """Generate a fake ISIN (12 chars: 2 country + 9 base + 1 check)."""
    if cusip:
        base = cusip
    else:
        base = generate_cusip()
    check = random.choice(string.digits)
    return f"{country}{base}{check}"


def generate_sedol():
    """Generate a fake SEDOL (7 chars alphanumeric)."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=7))


def random_price(asset_class):
    """Generate realistic price based on asset class."""
    if asset_class == "equity":
        return round(random.uniform(10, 500), 2)
    elif asset_class == "fixed_income":
        return round(random.uniform(85, 115), 4)  # Bond prices around par
    elif asset_class == "option":
        return round(random.uniform(0.5, 50), 2)
    elif asset_class == "future":
        return round(random.uniform(50, 5000), 2)
    else:
        return round(random.uniform(10, 1000), 2)


def random_quantity(direction, asset_class):
    """Generate realistic position quantity.

    Target position sizes (market value):
    - Equity: $100K - $5M
    - Fixed Income: $500K - $10M
    - Options: $50K - $500K
    - Futures: $100K - $2M
    """
    if asset_class == "equity":
        # For $10-500 stock, 200-10000 shares = $2K-$5M
        base = random.randint(200, 10000)
    elif asset_class == "option":
        # Option contracts (100 shares each), 5-100 contracts
        base = random.randint(5, 100) * 100
    elif asset_class == "future":
        # Futures contracts, 1-20 contracts
        base = random.randint(1, 20)
    elif asset_class == "fixed_income":
        # Bond face value, $100K - $5M
        base = random.randint(100, 5000) * 1000
    else:
        base = random.randint(100, 5000)

    return base if direction == "long" else -base


def generate_greeks(asset_class, direction, quantity):
    """Generate realistic Greeks for derivatives."""
    if asset_class not in ("option", "future", "swap"):
        return {}

    sign = 1 if quantity > 0 else -1
    abs_qty = abs(quantity)

    return {
        "delta": round(sign * random.uniform(0.2, 0.8) * (abs_qty / 100), 4),
        "gamma": round(random.uniform(0.001, 0.05) * (abs_qty / 100), 6),
        "vega": round(random.uniform(5, 50) * (abs_qty / 100), 2),
        "theta": round(-random.uniform(1, 20) * (abs_qty / 100), 2),
        "rho": round(sign * random.uniform(0.1, 5) * (abs_qty / 100), 2),
    }


def generate_fixed_income_risk(asset_class, quantity):
    """Generate DV01, CS01, convexity for fixed income."""
    if asset_class != "fixed_income":
        return {}

    notional = abs(quantity)
    return {
        "dv01": round(notional * random.uniform(0.0001, 0.001), 2),
        "cs01": round(notional * random.uniform(0.00005, 0.0005), 2),
        "convexity": round(random.uniform(0.5, 2.5), 4),
    }


# ============================================
# DATA GENERATORS
# ============================================

class MockDataGenerator:
    def __init__(self, conn, scale="medium"):
        self.conn = conn
        self.scale = SCALES[scale]
        self.scale_name = scale

        # Store generated IDs for relationships
        self.tenant_id = None
        self.user_ids = []
        self.pm_user_ids = []
        self.fund_ids = []
        self.book_ids = []
        self.security_ids = []
        self.position_ids = []

    def clean_data(self):
        """Remove all generated mock data."""
        print("Cleaning existing data...")
        cur = self.conn.cursor()

        # Delete in order respecting FKs
        tables = [
            "validation_results",
            "upload_records",
            "uploads",
            "notifications",
            "risk_metric_history",
            "risk_metrics",
            "limit_breaches",
            "limits",
            "position_changes",
            "position_history",
            "positions",
            "trades",
            "security_prices",
            "security_identifiers",
            "securities",
            "factor_exposures",
            "correlation_matrices",
            "model_overrides",
            "saved_views",
            "book_user_access",
            "books",
            "funds",
            "api_keys",
            "pending_invitations",
            "audit_logs",
            "users",
            "tenants",
        ]

        for table in tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                print(f"  Cleaned {table}")
            except Exception as e:
                print(f"  Warning: Could not clean {table}: {e}")
                self.conn.rollback()

        self.conn.commit()
        print("Data cleaned.\n")

    def generate_all(self):
        """Generate all mock data."""
        print(f"Generating {self.scale_name} scale mock data...")
        print(f"  PMs: {self.scale['num_pms']}")
        print(f"  Securities: {self.scale['num_securities']}")
        print(f"  Positions per book: ~{self.scale['positions_per_book']}")
        print()

        self._generate_tenant()
        self._generate_users()
        self._generate_funds_and_books()
        self._generate_securities()
        self._generate_security_prices()
        self._generate_positions()
        self._generate_trades()
        self._generate_risk_metrics()
        self._generate_limits()
        self._generate_limit_breaches()
        self._generate_book_user_access()

        self.conn.commit()
        print("\nMock data generation complete!")
        self._print_summary()

    def _generate_tenant(self):
        """Generate the tenant."""
        print("Generating tenant...")
        cur = self.conn.cursor()

        self.tenant_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO tenants (id, name, slug, plan, max_users, max_books, api_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            self.tenant_id,
            "Apex Capital Management",
            "apex-capital",
            "pro",
            50,
            25,
            True,
        ))
        print(f"  Created tenant: Apex Capital Management")

    def _generate_users(self):
        """Generate users with various roles."""
        print("Generating users...")
        cur = self.conn.cursor()

        # Admin user
        admin_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (id, tenant_id, email, name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (admin_id, self.tenant_id, "admin@apexcapital.com", "Admin User", "admin", True))
        self.user_ids.append(admin_id)

        # CIO
        cio_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (id, tenant_id, email, name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cio_id, self.tenant_id, "cio@apexcapital.com", "Margaret Chen", "cio", True))
        self.user_ids.append(cio_id)

        # CRO
        cro_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (id, tenant_id, email, name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cro_id, self.tenant_id, "cro@apexcapital.com", "Richard Torres", "cro", True))
        self.user_ids.append(cro_id)

        # PMs
        used_names = set()
        for i in range(self.scale["num_pms"]):
            pm_id = str(uuid.uuid4())

            # Generate unique name
            while True:
                first = random.choice(PM_FIRST_NAMES)
                last = random.choice(PM_LAST_NAMES)
                full_name = f"{first} {last}"
                if full_name not in used_names:
                    used_names.add(full_name)
                    break

            email = f"{first.lower()}.{last.lower()}@apexcapital.com"

            cur.execute("""
                INSERT INTO users (id, tenant_id, email, name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pm_id, self.tenant_id, email, full_name, "pm", True))

            self.user_ids.append(pm_id)
            self.pm_user_ids.append((pm_id, full_name))

        # Analysts
        for i in range(3):
            analyst_id = str(uuid.uuid4())
            first = random.choice(PM_FIRST_NAMES)
            last = random.choice(PM_LAST_NAMES)

            cur.execute("""
                INSERT INTO users (id, tenant_id, email, name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                analyst_id, self.tenant_id,
                f"analyst{i+1}@apexcapital.com",
                f"{first} {last}",
                "analyst", True
            ))
            self.user_ids.append(analyst_id)

        print(f"  Created {len(self.user_ids)} users ({len(self.pm_user_ids)} PMs)")

    def _generate_funds_and_books(self):
        """Generate funds and books (one book per PM)."""
        print("Generating funds and books...")
        cur = self.conn.cursor()

        # Create 2-3 funds
        fund_names = ["Alpha Fund", "Beta Fund", "Gamma Fund"]
        num_funds = min(3, max(2, self.scale["num_pms"] // 4))

        for i in range(num_funds):
            fund_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO funds (id, tenant_id, name, description, fund_type, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                fund_id, self.tenant_id,
                fund_names[i],
                f"Multi-strategy hedge fund - {fund_names[i]}",
                "hedge_fund",
                True
            ))
            self.fund_ids.append(fund_id)

        # Create one book per PM
        for idx, (pm_id, pm_name) in enumerate(self.pm_user_ids):
            book_id = str(uuid.uuid4())
            fund_id = self.fund_ids[idx % len(self.fund_ids)]
            strategy = random.choice(STRATEGIES)

            # Book name based on PM
            last_name = pm_name.split()[-1]
            book_name = f"{last_name} - {strategy}"

            cur.execute("""
                INSERT INTO books (id, tenant_id, fund_id, pm_id, name, description, strategy, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                book_id, self.tenant_id, fund_id, pm_id,
                book_name,
                f"Trading book managed by {pm_name}",
                strategy,
                True
            ))
            self.book_ids.append((book_id, book_name, pm_id))

        print(f"  Created {len(self.fund_ids)} funds, {len(self.book_ids)} books")

    def _generate_securities(self):
        """Generate securities with identifiers."""
        print("Generating securities...")
        cur = self.conn.cursor()

        # Shuffle and pick companies
        companies = random.sample(COMPANIES, min(len(COMPANIES), self.scale["num_securities"]))

        # If we need more, generate synthetic ones
        while len(companies) < self.scale["num_securities"]:
            suffix = len(companies) - len(COMPANIES) + 1
            ticker = f"SYN{suffix:03d}"
            companies.append((f"Synthetic Corp {suffix}", ticker, random.choice([
                "Technology", "Financials", "Healthcare", "Industrials", "Energy"
            ])))

        # Asset class distribution
        asset_classes = (
            ["equity"] * 60 +
            ["fixed_income"] * 15 +
            ["option"] * 10 +
            ["future"] * 10 +
            ["other"] * 5
        )

        for idx, (name, ticker, sector) in enumerate(companies):
            security_id = str(uuid.uuid4())
            asset_class = random.choice(asset_classes)
            country = random.choice(COUNTRIES)
            currency = "USD" if country == "USA" else random.choice(CURRENCIES)
            exchange = random.choice(EXCHANGES)

            figi = generate_figi()

            # Insert security
            cur.execute("""
                INSERT INTO securities (
                    id, figi, name, asset_class, security_type,
                    country_of_risk, country_of_domicile, sector, currency,
                    exchange_code, is_active, is_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                security_id, figi, name, asset_class,
                f"{asset_class}_common" if asset_class == "equity" else asset_class,
                country, country, sector, currency, exchange, True, True
            ))

            # Insert identifiers
            cusip = generate_cusip()
            isin = generate_isin("US", cusip)
            sedol = generate_sedol()

            identifiers = [
                (security_id, "figi", figi, exchange, True),
                (security_id, "ticker", ticker, exchange, False),
                (security_id, "cusip", cusip, None, False),
                (security_id, "isin", isin, None, False),
                (security_id, "sedol", sedol, exchange, False),
            ]

            for sec_id, id_type, id_value, exch, is_primary in identifiers:
                cur.execute("""
                    INSERT INTO security_identifiers (security_id, identifier_type, identifier_value, exchange_code, is_primary)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sec_id, id_type, id_value, exch, is_primary))

            self.security_ids.append((security_id, name, ticker, asset_class, currency))

        print(f"  Created {len(self.security_ids)} securities with identifiers")

    def _generate_security_prices(self):
        """Generate historical prices for securities."""
        print("Generating security prices...")
        cur = self.conn.cursor()

        today = date.today()
        num_days = self.scale["days_of_prices"]

        price_data = []
        for security_id, name, ticker, asset_class, currency in self.security_ids:
            base_price = random_price(asset_class)

            for day_offset in range(num_days):
                price_date = today - timedelta(days=day_offset)

                # Skip weekends
                if price_date.weekday() >= 5:
                    continue

                # Random walk for price
                daily_return = random.gauss(0, 0.02)  # 2% daily vol
                price = base_price * (1 + daily_return * (num_days - day_offset) / num_days)
                price = max(0.01, round(price, 4))

                price_data.append((
                    security_id,
                    price_date,
                    None,  # price_time
                    price,
                    round(price * 0.999, 4),  # bid
                    round(price * 1.001, 4),  # ask
                    random.randint(10000, 10000000),  # volume
                    "market",
                    True,  # is_adjusted
                ))

        # Batch insert
        execute_values(cur, """
            INSERT INTO security_prices (security_id, price_date, price_time, price, bid_price, ask_price, volume, source, is_adjusted)
            VALUES %s
        """, price_data)

        print(f"  Created {len(price_data)} price records")

    def _generate_positions(self):
        """Generate positions for each book."""
        print("Generating positions...")
        cur = self.conn.cursor()

        today = datetime.now()

        for book_id, book_name, pm_id in self.book_ids:
            # Each book gets a random subset of securities
            num_positions = random.randint(
                int(self.scale["positions_per_book"] * 0.7),
                int(self.scale["positions_per_book"] * 1.3)
            )
            book_securities = random.sample(
                self.security_ids,
                min(num_positions, len(self.security_ids))
            )

            for security_id, sec_name, ticker, asset_class, currency in book_securities:
                position_id = str(uuid.uuid4())

                # 70% long, 30% short
                direction = "long" if random.random() < 0.7 else "short"
                quantity = random_quantity(direction, asset_class)

                # Get latest price
                cur.execute("""
                    SELECT price FROM security_prices
                    WHERE security_id = %s
                    ORDER BY price_date DESC LIMIT 1
                """, (security_id,))
                result = cur.fetchone()
                price = result[0] if result else random_price(asset_class)

                # Calculate market value based on asset class
                if asset_class == "fixed_income":
                    # Bond price is % of par, quantity is face value
                    # E.g., $1M face value at 98.5 price = $985,000 market value
                    market_value = abs(quantity) * (float(price) / 100)
                else:
                    # Equity, options, futures: quantity * price
                    market_value = abs(quantity * float(price))

                cost_basis = market_value * random.uniform(0.85, 1.15)
                unrealized_pnl = market_value - cost_basis

                # Greeks and fixed income risk
                greeks = generate_greeks(asset_class, direction, quantity)
                fi_risk = generate_fixed_income_risk(asset_class, quantity)

                cur.execute("""
                    INSERT INTO positions (
                        id, tenant_id, book_id, security_id, quantity, direction,
                        market_value, cost_basis, unrealized_pnl, price, price_source,
                        local_currency, base_currency, market_value_base,
                        delta, gamma, vega, theta, rho, dv01, cs01, convexity,
                        source, as_of_timestamp
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                """, (
                    position_id, self.tenant_id, book_id, security_id,
                    quantity, direction,
                    round(market_value, 2), round(cost_basis, 2), round(unrealized_pnl, 2),
                    price, "market",
                    currency, "USD", round(market_value, 2),
                    greeks.get("delta"), greeks.get("gamma"), greeks.get("vega"),
                    greeks.get("theta"), greeks.get("rho"),
                    fi_risk.get("dv01"), fi_risk.get("cs01"), fi_risk.get("convexity"),
                    "file_upload", today
                ))

                self.position_ids.append(position_id)

        print(f"  Created {len(self.position_ids)} positions")

    def _generate_trades(self):
        """Generate some historical trades."""
        print("Generating trades...")
        cur = self.conn.cursor()

        today = date.today()
        num_trades = len(self.position_ids) // 2  # Roughly half as many trades as positions

        for _ in range(num_trades):
            book_id, book_name, pm_id = random.choice(self.book_ids)
            security_id, sec_name, ticker, asset_class, currency = random.choice(self.security_ids)

            trade_id = str(uuid.uuid4())
            side = random.choice(["buy", "sell", "short", "cover"])
            quantity = abs(random_quantity("long", asset_class))
            price = random_price(asset_class)
            trade_date = today - timedelta(days=random.randint(1, 60))

            cur.execute("""
                INSERT INTO trades (
                    id, tenant_id, book_id, security_id,
                    trade_id_external, side, quantity, price, notional,
                    currency, trade_date, settlement_date,
                    source, is_cancelled
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                trade_id, self.tenant_id, book_id, security_id,
                f"TRD-{random.randint(100000, 999999)}",
                side, quantity, price, round(quantity * price, 2),
                currency, trade_date, trade_date + timedelta(days=2),
                "file_upload", False
            ))

        print(f"  Created {num_trades} trades")

    def _generate_risk_metrics(self):
        """Generate risk metrics for books."""
        print("Generating risk metrics...")
        cur = self.conn.cursor()

        today = datetime.now()

        metric_types = [
            "var_95", "var_99", "cvar_95", "cvar_99",
            "gross_exposure", "net_exposure", "long_exposure", "short_exposure",
            "net_delta", "net_gamma", "net_vega", "total_dv01",
        ]

        for book_id, book_name, pm_id in self.book_ids:
            # Get book's total market value for scaling
            cur.execute("""
                SELECT COALESCE(SUM(ABS(market_value_base)), 1000000)
                FROM positions WHERE book_id = %s
            """, (book_id,))
            total_mv = float(cur.fetchone()[0])

            for metric_type in metric_types:
                metric_id = str(uuid.uuid4())

                # Generate realistic values
                if metric_type.startswith("var"):
                    value = total_mv * random.uniform(0.01, 0.05)  # 1-5% VaR
                elif metric_type.startswith("cvar"):
                    value = total_mv * random.uniform(0.02, 0.08)  # 2-8% CVaR
                elif metric_type == "gross_exposure":
                    value = total_mv * random.uniform(1.5, 3.0)  # 150-300% gross
                elif metric_type == "net_exposure":
                    value = total_mv * random.uniform(-0.3, 0.7)  # -30% to 70% net
                elif metric_type == "long_exposure":
                    value = total_mv * random.uniform(0.8, 1.5)
                elif metric_type == "short_exposure":
                    value = total_mv * random.uniform(0.3, 0.8)
                elif "delta" in metric_type or "gamma" in metric_type or "vega" in metric_type:
                    value = random.uniform(-10000, 10000)
                elif "dv01" in metric_type:
                    value = random.uniform(1000, 50000)
                else:
                    value = random.uniform(0, total_mv)

                cur.execute("""
                    INSERT INTO risk_metrics (
                        id, tenant_id, level, book_id, metric_type, value,
                        as_of_timestamp, is_valid
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    metric_id, self.tenant_id, "book", book_id,
                    metric_type, round(value, 2), today, True
                ))

        print(f"  Created {len(self.book_ids) * len(metric_types)} risk metrics")

    def _generate_limits(self):
        """Generate risk limits."""
        print("Generating limits...")
        cur = self.conn.cursor()

        # Firm-wide limits
        firm_limits = [
            ("Firm Gross Exposure", "gross_exposure", 5.0, 4.5, "tenant"),
            ("Firm Net Exposure", "net_exposure", 1.0, 0.8, "tenant"),
            ("Firm VaR 95%", "var_95", 0.05, 0.04, "tenant"),
        ]

        for name, metric_type, limit_val, warning, scope in firm_limits:
            limit_id = str(uuid.uuid4())
            # Get approximate firm AUM
            cur.execute("""
                SELECT COALESCE(SUM(ABS(market_value_base)), 10000000) FROM positions
                WHERE tenant_id = %s
            """, (self.tenant_id,))
            firm_aum = float(cur.fetchone()[0])

            cur.execute("""
                INSERT INTO limits (
                    id, tenant_id, name, scope, metric_type,
                    limit_type, limit_value, warning_threshold, is_upper_limit, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                limit_id, self.tenant_id, name, scope, metric_type,
                "hard", round(firm_aum * limit_val, 2), round(firm_aum * warning, 2), True, True
            ))

        # Book-level limits
        for book_id, book_name, pm_id in self.book_ids:
            cur.execute("""
                SELECT COALESCE(SUM(ABS(market_value_base)), 1000000) FROM positions
                WHERE book_id = %s
            """, (book_id,))
            book_mv = float(cur.fetchone()[0])

            # Concentration limit
            limit_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO limits (
                    id, tenant_id, name, scope, book_id, metric_type,
                    limit_type, limit_value, warning_threshold, is_upper_limit, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                limit_id, self.tenant_id, f"{book_name} - Max Position",
                "book", book_id, "single_name_max",
                "hard", round(book_mv * 0.10, 2), round(book_mv * 0.08, 2), True, True
            ))

        print(f"  Created {3 + len(self.book_ids)} limits")

    def _generate_limit_breaches(self):
        """Generate some limit breaches for testing alerts."""
        print("Generating limit breaches...")
        cur = self.conn.cursor()

        # Get some limits to breach
        cur.execute("""
            SELECT id, tenant_id, limit_value FROM limits
            WHERE tenant_id = %s LIMIT 3
        """, (self.tenant_id,))
        limits = cur.fetchall()

        for limit_id, tenant_id, limit_value in limits[:2]:  # Breach 2 limits
            breach_id = str(uuid.uuid4())
            actual_value = float(limit_value) * random.uniform(1.05, 1.20)
            breach_amount = actual_value - float(limit_value)

            cur.execute("""
                INSERT INTO limit_breaches (
                    id, tenant_id, limit_id, breach_timestamp,
                    limit_value, actual_value, breach_amount, breach_percentage,
                    status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                breach_id, tenant_id, limit_id, datetime.now() - timedelta(hours=random.randint(1, 48)),
                limit_value, round(actual_value, 2), round(breach_amount, 2),
                round((breach_amount / float(limit_value)) * 100, 2),
                random.choice(["active", "acknowledged"])
            ))

        print(f"  Created 2 limit breaches")

    def _generate_book_user_access(self):
        """Generate book access for PMs and analysts."""
        print("Generating book access...")
        cur = self.conn.cursor()

        # Each PM has access to their own book
        for book_id, book_name, pm_id in self.book_ids:
            access_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO book_user_access (id, book_id, user_id, access_level)
                VALUES (%s, %s, %s, %s)
            """, (access_id, book_id, pm_id, "write"))

        # Analysts get read access to a few books
        analyst_ids = [uid for uid in self.user_ids if uid not in [pm_id for pm_id, _ in self.pm_user_ids]]
        for analyst_id in analyst_ids[-3:]:  # Last 3 are analysts
            assigned_books = random.sample(self.book_ids, min(3, len(self.book_ids)))
            for book_id, _, _ in assigned_books:
                access_id = str(uuid.uuid4())
                try:
                    cur.execute("""
                        INSERT INTO book_user_access (id, book_id, user_id, access_level)
                        VALUES (%s, %s, %s, %s)
                    """, (access_id, book_id, analyst_id, "read"))
                except:
                    pass  # Ignore duplicates

        print(f"  Created book access records")

    def _print_summary(self):
        """Print summary of generated data."""
        cur = self.conn.cursor()

        print("\n" + "="*50)
        print("MOCK DATA SUMMARY")
        print("="*50)

        tables = [
            "tenants", "users", "funds", "books", "securities",
            "security_identifiers", "security_prices", "positions",
            "trades", "risk_metrics", "limits", "limit_breaches",
            "book_user_access"
        ]

        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count:,}")

        print("="*50)


# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Generate RISKCORE mock data")
    parser.add_argument("--clean", action="store_true", help="Clean existing data before generating")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="medium", help="Data scale")
    parser.add_argument("--clean-only", action="store_true", help="Only clean data, don't generate")
    args = parser.parse_args()

    print("RISKCORE Mock Data Generator")
    print("="*50)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        print(f"Connected to database\n")
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        print(f"Make sure Supabase is running: supabase start")
        sys.exit(1)

    try:
        generator = MockDataGenerator(conn, args.scale)

        if args.clean or args.clean_only:
            generator.clean_data()

        if not args.clean_only:
            generator.generate_all()

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
