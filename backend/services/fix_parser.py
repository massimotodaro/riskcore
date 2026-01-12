# RISKCORE FIX Protocol Parser
# Uses simplefix for FIX message parsing
# Supports ExecutionReport (35=8) and PositionReport (35=AP)

import simplefix
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime, date, time
import logging

logger = logging.getLogger(__name__)


# FIX Tag Constants
class FIXTags:
    """Common FIX protocol tags."""

    # Header
    BEGIN_STRING = 8
    MSG_TYPE = 35
    SENDER_COMP_ID = 49
    TARGET_COMP_ID = 56
    MSG_SEQ_NUM = 34
    SENDING_TIME = 52

    # Common
    ACCOUNT = 1
    SYMBOL = 55
    SECURITY_ID = 48
    SECURITY_ID_SOURCE = 22
    CURRENCY = 15

    # Order/Execution
    CL_ORD_ID = 11
    ORDER_ID = 37
    EXEC_ID = 17
    SIDE = 54
    ORDER_QTY = 38
    PRICE = 44
    LAST_QTY = 32
    LAST_PX = 31
    CUM_QTY = 14
    AVG_PX = 6
    ORD_STATUS = 39
    EXEC_TYPE = 150
    TRANSACT_TIME = 60
    TRADE_DATE = 75

    # Position Report
    POS_REQ_ID = 710
    POS_MAINT_RPT_ID = 721
    LONG_QTY = 704
    SHORT_QTY = 705
    SETTL_PRICE = 730

    # Identifiers
    CUSIP = 22  # SecurityIDSource=1
    ISIN = 22   # SecurityIDSource=4
    SEDOL = 22  # SecurityIDSource=2


# FIX Side values
class FIXSide:
    """FIX Side (tag 54) values."""
    BUY = "1"
    SELL = "2"
    BUY_MINUS = "3"
    SELL_PLUS = "4"
    SELL_SHORT = "5"
    SELL_SHORT_EXEMPT = "6"

    @classmethod
    def to_trade_side(cls, fix_side: str) -> str:
        """Convert FIX side to RISKCORE trade side."""
        mapping = {
            cls.BUY: "buy",
            cls.SELL: "sell",
            cls.BUY_MINUS: "buy",
            cls.SELL_PLUS: "sell",
            cls.SELL_SHORT: "short",
            cls.SELL_SHORT_EXEMPT: "short",
        }
        return mapping.get(fix_side, "buy")


# FIX Order Status values
class FIXOrdStatus:
    """FIX OrdStatus (tag 39) values."""
    NEW = "0"
    PARTIALLY_FILLED = "1"
    FILLED = "2"
    DONE_FOR_DAY = "3"
    CANCELED = "4"
    REPLACED = "5"
    PENDING_CANCEL = "6"
    STOPPED = "7"
    REJECTED = "8"
    SUSPENDED = "9"
    PENDING_NEW = "A"
    CALCULATED = "B"
    EXPIRED = "C"


# FIX Message Types
class FIXMsgType:
    """FIX MsgType (tag 35) values."""
    HEARTBEAT = "0"
    LOGON = "A"
    LOGOUT = "5"
    NEW_ORDER_SINGLE = "D"
    EXECUTION_REPORT = "8"
    ORDER_CANCEL_REQUEST = "F"
    ORDER_CANCEL_REPLACE = "G"
    ORDER_STATUS_REQUEST = "H"
    POSITION_REPORT = "AP"
    REQUEST_FOR_POSITIONS = "AN"


# SecurityIDSource values
class FIXSecurityIDSource:
    """FIX SecurityIDSource (tag 22) values."""
    CUSIP = "1"
    SEDOL = "2"
    QUIK = "3"
    ISIN = "4"
    RIC = "5"
    TICKER = "8"


class FIXParser:
    """
    FIX protocol message parser.

    Parses FIX messages and extracts trade/position data for RISKCORE.
    Supports:
    - ExecutionReport (35=8): Trade executions
    - PositionReport (35=AP): Position snapshots
    """

    def __init__(self):
        self.parser = simplefix.FixParser()

    def parse_message(self, raw_message: bytes) -> Dict[str, Any]:
        """
        Parse a single FIX message.

        Args:
            raw_message: Raw FIX message bytes

        Returns:
            Dict with parsed message data or error
        """
        try:
            self.parser.append_buffer(raw_message)
            message = self.parser.get_message()

            if not message:
                return {
                    "success": False,
                    "error": "Could not parse FIX message",
                }

            # Get message type
            msg_type = self._get_field(message, FIXTags.MSG_TYPE)

            if msg_type == FIXMsgType.EXECUTION_REPORT:
                return self._parse_execution_report(message)
            elif msg_type == FIXMsgType.POSITION_REPORT:
                return self._parse_position_report(message)
            else:
                return {
                    "success": True,
                    "msg_type": msg_type,
                    "message": "Message type not supported for data extraction",
                    "supported": False,
                }

        except Exception as e:
            logger.error(f"Error parsing FIX message: {e}")
            return {
                "success": False,
                "error": f"Parse error: {str(e)}",
            }

    def parse_messages(self, raw_data: bytes) -> List[Dict[str, Any]]:
        """
        Parse multiple FIX messages from a buffer.

        Args:
            raw_data: Raw bytes containing one or more FIX messages

        Returns:
            List of parsed message dicts
        """
        results = []
        self.parser.append_buffer(raw_data)

        while True:
            try:
                message = self.parser.get_message()
                if not message:
                    break

                msg_type = self._get_field(message, FIXTags.MSG_TYPE)

                if msg_type == FIXMsgType.EXECUTION_REPORT:
                    results.append(self._parse_execution_report(message))
                elif msg_type == FIXMsgType.POSITION_REPORT:
                    results.append(self._parse_position_report(message))
                else:
                    results.append({
                        "success": True,
                        "msg_type": msg_type,
                        "supported": False,
                    })
            except Exception as e:
                logger.error(f"Error parsing message in batch: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                })

        return results

    def _parse_execution_report(self, message: simplefix.FixMessage) -> Dict[str, Any]:
        """
        Parse ExecutionReport (35=8) message.

        Extracts trade execution data.
        """
        try:
            # Required fields
            symbol = self._get_field(message, FIXTags.SYMBOL)
            side = self._get_field(message, FIXTags.SIDE)

            # Quantity - prefer LastQty (actual fill), fall back to CumQty or OrderQty
            quantity = (
                self._get_decimal(message, FIXTags.LAST_QTY) or
                self._get_decimal(message, FIXTags.CUM_QTY) or
                self._get_decimal(message, FIXTags.ORDER_QTY)
            )

            # Price - prefer LastPx (actual fill price), fall back to AvgPx or Price
            price = (
                self._get_decimal(message, FIXTags.LAST_PX) or
                self._get_decimal(message, FIXTags.AVG_PX) or
                self._get_decimal(message, FIXTags.PRICE)
            )

            if not symbol:
                return {
                    "success": False,
                    "error": "Missing required field: Symbol (55)",
                    "msg_type": FIXMsgType.EXECUTION_REPORT,
                }

            # Build trade data
            trade_data = {
                "success": True,
                "msg_type": FIXMsgType.EXECUTION_REPORT,
                "supported": True,
                "data_type": "trade",
                "data": {
                    "ticker": symbol,
                    "side": FIXSide.to_trade_side(side) if side else "buy",
                    "quantity": quantity,
                    "price": price,
                    "currency": self._get_field(message, FIXTags.CURRENCY) or "USD",
                    "trade_date": self._parse_trade_date(message),
                    "trade_time": self._parse_trade_time(message),
                    "trade_id_external": self._get_field(message, FIXTags.EXEC_ID),
                    "order_id_external": self._get_field(message, FIXTags.ORDER_ID) or self._get_field(message, FIXTags.CL_ORD_ID),
                    "broker": self._get_field(message, FIXTags.SENDER_COMP_ID),
                    "counterparty": self._get_field(message, FIXTags.TARGET_COMP_ID),
                    "account": self._get_field(message, FIXTags.ACCOUNT),
                    "ord_status": self._get_field(message, FIXTags.ORD_STATUS),
                    "exec_type": self._get_field(message, FIXTags.EXEC_TYPE),
                },
            }

            # Add security identifiers if present
            security_id = self._get_field(message, FIXTags.SECURITY_ID)
            security_id_source = self._get_field(message, FIXTags.SECURITY_ID_SOURCE)

            if security_id and security_id_source:
                if security_id_source == FIXSecurityIDSource.CUSIP:
                    trade_data["data"]["cusip"] = security_id
                elif security_id_source == FIXSecurityIDSource.ISIN:
                    trade_data["data"]["isin"] = security_id
                elif security_id_source == FIXSecurityIDSource.SEDOL:
                    trade_data["data"]["sedol"] = security_id

            return trade_data

        except Exception as e:
            logger.error(f"Error parsing ExecutionReport: {e}")
            return {
                "success": False,
                "error": f"ExecutionReport parse error: {str(e)}",
                "msg_type": FIXMsgType.EXECUTION_REPORT,
            }

    def _parse_position_report(self, message: simplefix.FixMessage) -> Dict[str, Any]:
        """
        Parse PositionReport (35=AP) message.

        Extracts position snapshot data.
        """
        try:
            symbol = self._get_field(message, FIXTags.SYMBOL)

            if not symbol:
                return {
                    "success": False,
                    "error": "Missing required field: Symbol (55)",
                    "msg_type": FIXMsgType.POSITION_REPORT,
                }

            # Get quantities
            long_qty = self._get_decimal(message, FIXTags.LONG_QTY) or Decimal("0")
            short_qty = self._get_decimal(message, FIXTags.SHORT_QTY) or Decimal("0")

            # Determine direction and net quantity
            if long_qty > 0 and short_qty == 0:
                direction = "long"
                quantity = long_qty
            elif short_qty > 0 and long_qty == 0:
                direction = "short"
                quantity = short_qty
            elif long_qty > short_qty:
                direction = "long"
                quantity = long_qty - short_qty
            else:
                direction = "short"
                quantity = short_qty - long_qty

            # Build position data
            position_data = {
                "success": True,
                "msg_type": FIXMsgType.POSITION_REPORT,
                "supported": True,
                "data_type": "position",
                "data": {
                    "ticker": symbol,
                    "quantity": quantity,
                    "direction": direction,
                    "long_qty": long_qty,
                    "short_qty": short_qty,
                    "price": self._get_decimal(message, FIXTags.SETTL_PRICE),
                    "currency": self._get_field(message, FIXTags.CURRENCY) or "USD",
                    "account": self._get_field(message, FIXTags.ACCOUNT),
                    "pos_req_id": self._get_field(message, FIXTags.POS_REQ_ID),
                    "pos_maint_rpt_id": self._get_field(message, FIXTags.POS_MAINT_RPT_ID),
                },
            }

            # Add security identifiers if present
            security_id = self._get_field(message, FIXTags.SECURITY_ID)
            security_id_source = self._get_field(message, FIXTags.SECURITY_ID_SOURCE)

            if security_id and security_id_source:
                if security_id_source == FIXSecurityIDSource.CUSIP:
                    position_data["data"]["cusip"] = security_id
                elif security_id_source == FIXSecurityIDSource.ISIN:
                    position_data["data"]["isin"] = security_id
                elif security_id_source == FIXSecurityIDSource.SEDOL:
                    position_data["data"]["sedol"] = security_id

            return position_data

        except Exception as e:
            logger.error(f"Error parsing PositionReport: {e}")
            return {
                "success": False,
                "error": f"PositionReport parse error: {str(e)}",
                "msg_type": FIXMsgType.POSITION_REPORT,
            }

    def _get_field(self, message: simplefix.FixMessage, tag: int) -> Optional[str]:
        """Get string field value from message."""
        try:
            value = message.get(tag)
            if value is not None:
                # simplefix returns bytes, decode to string
                if isinstance(value, bytes):
                    return value.decode("utf-8")
                return str(value)
            return None
        except Exception:
            return None

    def _get_decimal(self, message: simplefix.FixMessage, tag: int) -> Optional[Decimal]:
        """Get decimal field value from message."""
        value = self._get_field(message, tag)
        if value:
            try:
                return Decimal(value)
            except Exception:
                return None
        return None

    def _parse_trade_date(self, message: simplefix.FixMessage) -> Optional[date]:
        """Parse trade date from TradeDate (75) or TransactTime (60)."""
        # Try TradeDate first (YYYYMMDD format)
        trade_date_str = self._get_field(message, FIXTags.TRADE_DATE)
        if trade_date_str:
            try:
                return datetime.strptime(trade_date_str, "%Y%m%d").date()
            except ValueError:
                pass

        # Fall back to TransactTime
        transact_time = self._get_field(message, FIXTags.TRANSACT_TIME)
        if transact_time:
            try:
                # TransactTime format: YYYYMMDD-HH:MM:SS or YYYYMMDD-HH:MM:SS.sss
                dt = datetime.strptime(transact_time[:8], "%Y%m%d")
                return dt.date()
            except ValueError:
                pass

        return None

    def _parse_trade_time(self, message: simplefix.FixMessage) -> Optional[time]:
        """Parse trade time from TransactTime (60)."""
        transact_time = self._get_field(message, FIXTags.TRANSACT_TIME)
        if transact_time and len(transact_time) >= 15:
            try:
                # TransactTime format: YYYYMMDD-HH:MM:SS
                time_part = transact_time[9:17]  # HH:MM:SS
                return datetime.strptime(time_part, "%H:%M:%S").time()
            except ValueError:
                pass
        return None

    @staticmethod
    def create_sample_execution_report(
        symbol: str = "AAPL",
        side: str = "1",  # Buy
        quantity: int = 100,
        price: float = 150.50,
        currency: str = "USD",
        exec_id: str = "EXEC001",
    ) -> bytes:
        """
        Create a sample ExecutionReport message for testing.

        Returns raw FIX message bytes.
        """
        msg = simplefix.FixMessage()
        msg.append_pair(FIXTags.BEGIN_STRING, "FIX.4.4")
        msg.append_pair(FIXTags.MSG_TYPE, FIXMsgType.EXECUTION_REPORT)
        msg.append_pair(FIXTags.SENDER_COMP_ID, "BROKER")
        msg.append_pair(FIXTags.TARGET_COMP_ID, "CLIENT")
        msg.append_pair(FIXTags.MSG_SEQ_NUM, 1, header=True)
        msg.append_pair(FIXTags.EXEC_ID, exec_id)
        msg.append_pair(FIXTags.ORDER_ID, "ORD001")
        msg.append_pair(FIXTags.SYMBOL, symbol)
        msg.append_pair(FIXTags.SIDE, side)
        msg.append_pair(FIXTags.ORDER_QTY, quantity)
        msg.append_pair(FIXTags.LAST_QTY, quantity)
        msg.append_pair(FIXTags.LAST_PX, price)
        msg.append_pair(FIXTags.AVG_PX, price)
        msg.append_pair(FIXTags.CUM_QTY, quantity)
        msg.append_pair(FIXTags.CURRENCY, currency)
        msg.append_pair(FIXTags.ORD_STATUS, FIXOrdStatus.FILLED)
        msg.append_pair(FIXTags.EXEC_TYPE, "F")  # Fill
        msg.append_pair(FIXTags.TRADE_DATE, datetime.now().strftime("%Y%m%d"))
        msg.append_utc_timestamp(FIXTags.TRANSACT_TIME)

        return msg.encode()

    @staticmethod
    def create_sample_position_report(
        symbol: str = "AAPL",
        long_qty: int = 1000,
        short_qty: int = 0,
        price: float = 150.50,
        currency: str = "USD",
    ) -> bytes:
        """
        Create a sample PositionReport message for testing.

        Returns raw FIX message bytes.
        """
        msg = simplefix.FixMessage()
        msg.append_pair(FIXTags.BEGIN_STRING, "FIX.4.4")
        msg.append_pair(FIXTags.MSG_TYPE, FIXMsgType.POSITION_REPORT)
        msg.append_pair(FIXTags.SENDER_COMP_ID, "BROKER")
        msg.append_pair(FIXTags.TARGET_COMP_ID, "CLIENT")
        msg.append_pair(FIXTags.MSG_SEQ_NUM, 1, header=True)
        msg.append_pair(FIXTags.POS_REQ_ID, "POSREQ001")
        msg.append_pair(FIXTags.POS_MAINT_RPT_ID, "POSRPT001")
        msg.append_pair(FIXTags.SYMBOL, symbol)
        msg.append_pair(FIXTags.LONG_QTY, long_qty)
        msg.append_pair(FIXTags.SHORT_QTY, short_qty)
        msg.append_pair(FIXTags.SETTL_PRICE, price)
        msg.append_pair(FIXTags.CURRENCY, currency)
        msg.append_pair(FIXTags.ACCOUNT, "ACCT001")

        return msg.encode()
