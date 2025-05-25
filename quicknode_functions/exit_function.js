const axios = require('axios');

// Environment variables
const {
    WALLET_ADDRESS,
    STOP_LOSS_PERCENTAGE = 10,
    SLIPPAGE_BPS = 500  // Higher slippage for emergency exits
} = process.env;

const WSOL_MINT = "So11111111111111111111111111111111111111112";

// QuickNode Function handler for stop-loss triggers
async function main(params) {
    const { qnContext, event } = params;
    
    try {
        // Extract price data from Chainlink event
        const { mint, currentPrice } = extractPriceData(event);
        
        // Get position data from KV store
        const positionKey = `position_${mint}`;
        const position = await qnContext.kv.get(positionKey);
        
        if (!position) {
            return {
                status: 'skip',
                reason: 'No active position found'
            };
        }
        
        const { entryPrice, amount, orderPubkey } = position;
        
        // Calculate price change
        const priceChange = ((currentPrice - entryPrice) / entryPrice) * 100;
        
        // Check stop-loss condition
        if (priceChange > -STOP_LOSS_PERCENTAGE) {
            return {
                status: 'skip',
                reason: `Price change ${priceChange.toFixed(2)}% within threshold`
            };
        }
        
        console.log(`Stop-loss triggered for ${mint}: ${priceChange.toFixed(2)}%`);
        
        // Cancel limit order if exists
        if (orderPubkey) {
            await cancelLimitOrder(qnContext, orderPubkey);
        }
        
        // Get quote for market sell
        const quote = await getQuote(qnContext, mint, WSOL_MINT, amount);
        if (!quote) {
            return {
                status: 'error',
                reason: 'Failed to get sell quote'
            };
        }
        
        // Generate market sell transaction
        const sellTx = await generateSwap(qnContext, quote);
        if (!sellTx) {
            return {
                status: 'error',
                reason: 'Failed to generate sell transaction'
            };
        }
        
        // Clear position from KV store
        await qnContext.kv.delete(positionKey);
        
        return {
            status: 'success',
            action: 'stop_loss_executed',
            mint,
            priceChange: priceChange.toFixed(2),
            sellTransaction: sellTx,
            outAmount: quote.outAmount
        };
        
    } catch (error) {
        console.error('Error in exit function:', error);
        return {
            status: 'error',
            error: error.message
        };
    }
}

function extractPriceData(event) {
    // Parse Chainlink AnswerUpdated event
    // This is a simplified example - actual implementation depends on the aggregator
    
    // For demonstration, assuming event contains decoded data
    const mint = event.mint || event.params?.mint;
    const currentPrice = event.price || event.params?.price;
    
    return {
        mint,
        currentPrice: parseFloat(currentPrice)
    };
}

async function cancelLimitOrder(qnContext, orderPubkey) {
    try {
        const response = await axios.post(
            `${qnContext.apiEndpoint}/limit-orders/cancel`,
            {
                owner: WALLET_ADDRESS,
                orderPubkey
            }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error canceling limit order:', error);
        // Continue with market sell even if cancel fails
    }
}

async function getQuote(qnContext, inputMint, outputMint, amount) {
    try {
        const params = {
            inputMint,
            outputMint,
            amount: amount.toString(),
            slippageBps: SLIPPAGE_BPS.toString()
        };
        
        const response = await axios.get(
            `${qnContext.apiEndpoint}/quote`,
            { params }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error getting quote:', error);
        return null;
    }
}

async function generateSwap(qnContext, quote) {
    try {
        const response = await axios.post(
            `${qnContext.apiEndpoint}/swap`,
            {
                owner: WALLET_ADDRESS,
                quoteResponse: quote
            }
        );
        
        return response.data.swapTransaction;
    } catch (error) {
        console.error('Error generating swap:', error);
        return null;
    }
}

// Alternative: Monitor open orders and execute stop-loss based on current prices
async function monitorPositions(qnContext) {
    try {
        // Get all open limit orders
        const response = await axios.get(
            `${qnContext.apiEndpoint}/limit-orders/open`,
            { params: { wallet: WALLET_ADDRESS } }
        );
        
        const orders = response.data.orders || [];
        
        for (const order of orders) {
            const mint = order.inputMint;
            if (mint === WSOL_MINT) continue;
            
            // Get current price via quote
            const quote = await getQuote(
                qnContext,
                mint,
                WSOL_MINT,
                order.makingAmount
            );
            
            if (!quote) continue;
            
            // Retrieve entry price from KV store
            const position = await qnContext.kv.get(`position_${mint}`);
            if (!position) continue;
            
            const { entryPrice } = position;
            const currentValue = parseInt(quote.outAmount);
            const entryValue = parseInt(order.makingAmount) * entryPrice;
            
            const priceChange = ((currentValue - entryValue) / entryValue) * 100;
            
            if (priceChange <= -STOP_LOSS_PERCENTAGE) {
                // Trigger stop-loss
                await main({
                    qnContext,
                    event: {
                        mint,
                        price: currentValue / parseInt(order.makingAmount)
                    }
                });
            }
        }
        
    } catch (error) {
        console.error('Error monitoring positions:', error);
    }
}

module.exports = { main, monitorPositions }; 