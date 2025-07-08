# ML/AI Workflow Rules for Trading Bot

You are an expert in **Python ML/AI workflows**, **trading algorithm development**, **signal processing**, and **real-time data analysis**.

## AI-First Trading Bot Architecture

### Core ML/AI Principles
- **Real-time inference** - All ML models must support sub-second prediction times
- **Stateless design** - Models should not maintain internal state between predictions
- **Graceful degradation** - System must function with fallback logic when ML models fail
- **Continuous learning** - Support for model retraining with new market data
- **Feature engineering** - Robust preprocessing pipelines for market data

### ML Pipeline Structure
```
ml/
├── models/
│   ├── entry_signal_model.py      # Entry signal classification
│   ├── exit_timing_model.py       # Exit timing prediction
│   ├── risk_assessment_model.py   # Risk scoring
│   └── model_registry.py          # Model versioning and loading
├── features/
│   ├── price_features.py          # Price-based feature extraction
│   ├── volume_features.py         # Volume-based features
│   ├── technical_indicators.py   # Technical analysis features
│   └── market_sentiment.py       # Sentiment analysis features
├── preprocessing/
│   ├── data_pipeline.py          # Real-time data preprocessing
│   ├── feature_scaler.py         # Feature normalization
│   └── outlier_detection.py     # Anomaly detection
└── evaluation/
    ├── backtesting.py            # Strategy backtesting
    ├── model_metrics.py          # Model performance evaluation
    └── risk_metrics.py           # Trading risk assessment
```

## ML Model Development Standards

### Model Interface Protocol
```python
from typing import Protocol, Dict, Any, Optional
from pydantic import BaseModel
from decimal import Decimal
import numpy as np

class TradingModel(Protocol):
    """Protocol for all trading ML models."""
    
    async def predict(
        self,
        features: Dict[str, float]
    ) -> Dict[str, Union[float, bool, str]]: ...
    
    def get_feature_importance(self) -> Dict[str, float]: ...
    
    def get_model_metadata(self) -> Dict[str, Any]: ...

class ModelPrediction(BaseModel):
    """Standardized model prediction output."""
    prediction: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    features_used: List[str]
    prediction_timestamp: datetime
    execution_time_ms: float
```

### Real-Time Feature Engineering
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class MarketData:
    """Real-time market data point."""
    timestamp: datetime
    price: Decimal
    volume: Decimal
    market_cap: Optional[Decimal] = None
    liquidity: Optional[Decimal] = None

class FeatureExtractor:
    """Extract trading features from real-time market data."""
    
    def __init__(self, lookback_periods: List[int] = [5, 15, 30, 60]):
        self.lookback_periods = lookback_periods
        self.price_history = deque(maxlen=max(lookback_periods))
        self.volume_history = deque(maxlen=max(lookback_periods))
    
    async def extract_features(
        self,
        current_data: MarketData,
        token_address: str
    ) -> Dict[str, float]:
        """Extract features for ML model prediction.
        
        Args:
            current_data: Current market data point
            token_address: Token being analyzed
            
        Returns:
            Dictionary of extracted features
        """
        self.price_history.append(current_data.price)
        self.volume_history.append(current_data.volume)
        
        features = {}
        
        # Price-based features
        features.update(self._extract_price_features())
        
        # Volume-based features  
        features.update(self._extract_volume_features())
        
        # Technical indicators
        features.update(self._extract_technical_indicators())
        
        # Market structure features
        features.update(await self._extract_market_features(token_address))
        
        return features
    
    def _extract_price_features(self) -> Dict[str, float]:
        """Extract price-based technical features."""
        if len(self.price_history) < 2:
            return {}
            
        prices = np.array(self.price_history, dtype=float)
        
        return {
            "price_change_1m": float(prices[-1] / prices[-2] - 1) if len(prices) >= 2 else 0.0,
            "price_change_5m": float(prices[-1] / prices[-5] - 1) if len(prices) >= 5 else 0.0,
            "price_volatility_5m": float(np.std(prices[-5:])) if len(prices) >= 5 else 0.0,
            "price_momentum": float(np.mean(np.diff(prices))) if len(prices) >= 3 else 0.0,
            "price_rsi": self._calculate_rsi(prices) if len(prices) >= 14 else 50.0,
        }
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
```

### Model Training Pipeline
```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
from pathlib import Path

class TradingModelTrainer:
    """Training pipeline for trading ML models."""
    
    def __init__(
        self,
        model_name: str,
        experiment_name: str = "trading_bot_models"
    ):
        self.model_name = model_name
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
    
    async def train_entry_signal_model(
        self,
        training_data: pd.DataFrame,
        target_column: str = "profitable_entry"
    ) -> str:
        """Train entry signal classification model.
        
        Args:
            training_data: Historical market data with labels
            target_column: Name of target variable column
            
        Returns:
            Model version identifier
        """
        with mlflow.start_run(run_name=f"{self.model_name}_training"):
            # Log parameters
            mlflow.log_param("model_type", "RandomForestClassifier")
            mlflow.log_param("training_samples", len(training_data))
            
            # Prepare features and target
            feature_columns = [col for col in training_data.columns 
                             if col not in [target_column, "timestamp", "token_address"]]
            
            X = training_data[feature_columns]
            y = training_data[target_column]
            
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
            
            # Cross-validation
            cv_scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                
                accuracy = accuracy_score(y_val, y_pred)
                cv_scores.append(accuracy)
            
            # Log metrics
            mlflow.log_metric("cv_accuracy_mean", np.mean(cv_scores))
            mlflow.log_metric("cv_accuracy_std", np.std(cv_scores))
            
            # Final training on full dataset
            model.fit(X, y)
            
            # Feature importance
            feature_importance = dict(zip(feature_columns, model.feature_importances_))
            mlflow.log_dict(feature_importance, "feature_importance.json")
            
            # Save model
            model_path = f"models/{self.model_name}_v{mlflow.active_run().info.run_id}"
            mlflow.sklearn.log_model(model, "model")
            
            # Save locally for fast loading
            local_model_path = Path(f"ml/saved_models/{self.model_name}_latest.joblib")
            local_model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, local_model_path)
            
            return mlflow.active_run().info.run_id
```

### Real-Time Model Inference
```python
import asyncio
import joblib
from typing import Optional
import logging

class ModelInferenceEngine:
    """High-performance model inference for real-time trading."""
    
    def __init__(self, model_path: str, max_inference_time_ms: int = 100):
        self.model_path = model_path
        self.max_inference_time_ms = max_inference_time_ms
        self.model = None
        self.feature_scaler = None
        self.inference_count = 0
        self.total_inference_time = 0.0
    
    async def load_model(self) -> None:
        """Load model from disk asynchronously."""
        try:
            # Load in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, joblib.load, self.model_path
            )
            logging.info(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            raise ModelLoadError(f"Could not load model from {self.model_path}")
    
    async def predict(
        self,
        features: Dict[str, float],
        timeout_ms: Optional[int] = None
    ) -> ModelPrediction:
        """Make prediction with timeout protection.
        
        Args:
            features: Input features for prediction
            timeout_ms: Override default timeout
            
        Returns:
            Model prediction with metadata
            
        Raises:
            ModelInferenceError: If prediction fails or times out
        """
        if self.model is None:
            raise ModelInferenceError("Model not loaded")
        
        start_time = asyncio.get_event_loop().time()
        timeout = timeout_ms or self.max_inference_time_ms
        
        try:
            # Convert features to model input format
            feature_array = self._prepare_features(features)
            
            # Run prediction with timeout
            prediction_task = asyncio.get_event_loop().run_in_executor(
                None, self._predict_sync, feature_array
            )
            
            prediction_raw = await asyncio.wait_for(
                prediction_task,
                timeout=timeout / 1000.0
            )
            
            # Calculate execution time
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Update performance metrics
            self.inference_count += 1
            self.total_inference_time += execution_time
            
            # Create structured prediction
            prediction = ModelPrediction(
                prediction=float(prediction_raw[0]),
                confidence=float(prediction_raw[1]) if len(prediction_raw) > 1 else 0.8,
                model_version=self._get_model_version(),
                features_used=list(features.keys()),
                prediction_timestamp=datetime.utcnow(),
                execution_time_ms=execution_time
            )
            
            return prediction
            
        except asyncio.TimeoutError:
            raise ModelInferenceError(f"Prediction timeout after {timeout}ms")
        except Exception as e:
            raise ModelInferenceError(f"Prediction failed: {e}")
    
    def _predict_sync(self, features: np.ndarray) -> np.ndarray:
        """Synchronous prediction method."""
        if hasattr(self.model, 'predict_proba'):
            probas = self.model.predict_proba(features.reshape(1, -1))[0]
            return probas
        else:
            prediction = self.model.predict(features.reshape(1, -1))[0]
            return np.array([prediction])
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get model inference performance statistics."""
        if self.inference_count == 0:
            return {"avg_inference_time_ms": 0.0, "total_predictions": 0}
        
        return {
            "avg_inference_time_ms": self.total_inference_time / self.inference_count,
            "total_predictions": self.inference_count,
            "total_inference_time_ms": self.total_inference_time
        }
```

### Backtesting and Model Evaluation
```python
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class BacktestResult:
    """Results from strategy backtesting."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_duration_minutes: float
    model_accuracy: float

class TradingBacktester:
    """Backtest trading strategies with ML models."""
    
    def __init__(
        self,
        initial_balance: Decimal = Decimal("1000"),
        transaction_fee: float = 0.0025
    ):
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
    
    async def backtest_strategy(
        self,
        historical_data: pd.DataFrame,
        model: TradingModel,
        feature_extractor: FeatureExtractor
    ) -> BacktestResult:
        """Run comprehensive backtest of trading strategy.
        
        Args:
            historical_data: Historical price and volume data
            model: Trained ML model for signal generation
            feature_extractor: Feature extraction pipeline
            
        Returns:
            Detailed backtesting results
        """
        balance = self.initial_balance
        position = Decimal("0")
        trades = []
        
        for i, row in historical_data.iterrows():
            # Extract features for current time point
            market_data = MarketData(
                timestamp=row['timestamp'],
                price=Decimal(str(row['price'])),
                volume=Decimal(str(row['volume']))
            )
            
            features = await feature_extractor.extract_features(
                market_data, row['token_address']
            )
            
            # Get model prediction
            prediction = await model.predict(features)
            
            # Trading logic based on prediction
            if prediction['prediction'] > 0.7 and position == 0:
                # Enter position
                position = balance / market_data.price * (1 - self.transaction_fee)
                balance = Decimal("0")
                
                trades.append({
                    'entry_time': market_data.timestamp,
                    'entry_price': market_data.price,
                    'position_size': position,
                    'prediction_confidence': prediction['confidence']
                })
            
            elif prediction['prediction'] < 0.3 and position > 0:
                # Exit position
                balance = position * market_data.price * (1 - self.transaction_fee)
                
                # Update trade record
                if trades:
                    trades[-1].update({
                        'exit_time': market_data.timestamp,
                        'exit_price': market_data.price,
                        'profit_loss': balance - self.initial_balance,
                        'duration_minutes': (
                            market_data.timestamp - trades[-1]['entry_time']
                        ).total_seconds() / 60
                    })
                
                position = Decimal("0")
        
        # Calculate performance metrics
        return self._calculate_backtest_metrics(trades)
    
    def _calculate_backtest_metrics(self, trades: List[Dict]) -> BacktestResult:
        """Calculate comprehensive trading performance metrics."""
        completed_trades = [t for t in trades if 'exit_time' in t]
        
        if not completed_trades:
            return BacktestResult(
                total_return=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
                win_rate=0.0, total_trades=0, profitable_trades=0,
                avg_trade_duration_minutes=0.0, model_accuracy=0.0
            )
        
        # Calculate returns
        returns = [float(t['profit_loss']) for t in completed_trades]
        total_return = sum(returns) / float(self.initial_balance)
        
        profitable_trades = len([r for r in returns if r > 0])
        win_rate = profitable_trades / len(completed_trades)
        
        # Calculate Sharpe ratio (simplified)
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Calculate maximum drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        # Average trade duration
        durations = [t['duration_minutes'] for t in completed_trades]
        avg_duration = np.mean(durations) if durations else 0.0
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(completed_trades),
            profitable_trades=profitable_trades,
            avg_trade_duration_minutes=avg_duration,
            model_accuracy=win_rate  # Simplified metric
        )
```

## Model Monitoring and Maintenance

### Performance Monitoring
```python
class ModelMonitor:
    """Monitor ML model performance in production."""
    
    def __init__(self, alert_threshold: float = 0.1):
        self.alert_threshold = alert_threshold
        self.performance_history = deque(maxsize=1000)
    
    async def log_prediction_outcome(
        self,
        prediction: ModelPrediction,
        actual_outcome: bool,
        trade_result: Optional[TradeResult] = None
    ) -> None:
        """Log prediction vs actual outcome for monitoring."""
        outcome_record = {
            'timestamp': datetime.utcnow(),
            'predicted_probability': prediction.prediction,
            'actual_outcome': actual_outcome,
            'model_version': prediction.model_version,
            'trade_profitable': trade_result.success if trade_result else None
        }
        
        self.performance_history.append(outcome_record)
        
        # Check for model drift
        await self._check_model_performance()
    
    async def _check_model_performance(self) -> None:
        """Check for significant drops in model performance."""
        if len(self.performance_history) < 50:
            return
        
        recent_accuracy = self._calculate_recent_accuracy(window=50)
        baseline_accuracy = self._calculate_recent_accuracy(window=200)
        
        if baseline_accuracy - recent_accuracy > self.alert_threshold:
            await self._trigger_model_alert(recent_accuracy, baseline_accuracy)
    
    def _calculate_recent_accuracy(self, window: int) -> float:
        """Calculate model accuracy over recent window."""
        recent_records = list(self.performance_history)[-window:]
        if not recent_records:
            return 0.0
        
        correct_predictions = sum(
            1 for r in recent_records 
            if (r['predicted_probability'] > 0.5) == r['actual_outcome']
        )
        
        return correct_predictions / len(recent_records)
```

## Custom Exceptions for ML Pipeline
```python
class MLPipelineError(Exception):
    """Base exception for ML pipeline errors."""

class ModelLoadError(MLPipelineError):
    """Raised when model fails to load."""

class ModelInferenceError(MLPipelineError):
    """Raised when model inference fails."""

class FeatureExtractionError(MLPipelineError):
    """Raised when feature extraction fails."""

class ModelDriftError(MLPipelineError):
    """Raised when significant model drift is detected."""
``` 