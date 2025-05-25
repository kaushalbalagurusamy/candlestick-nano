const axios = require('axios');
const { PublicKey } = require('@solana/web3.js');

// Environment variables (configured in QuickNode Functions dashboard)
const {
    WALLET_ADDRESS,
    MIN_LIQUIDITY_THRESHOLD = 100000,
    MAX_TOKEN_AGE = 82800,
    SLIPPAGE_BPS = 100
} = process.env;

const WSOL_MINT = "So11111111111111111111111111111111111111112";

// QuickNode Function handler
async function main(params) {
    const { qnContext, pool } = params;
    
    try {
        // Extract pool data from event
        const mint = pool.tokenAddress;
        const timestamp = pool.timestamp;
        
        // Age check
        const poolTime = new Date(timestamp);
        const ageSeconds = (Date.now() - poolTime.getTime()) / 1000;
        
        if (ageSeconds > MAX_TOKEN_AGE) {
            return {
                status: 'skip',
                reason: `Token too old: ${ageSeconds / 3600} hours`
            };
        }
        
        // Check if already processed (using KV store)
        const processed = await qnContext.kv.get(`processed_${mint}`);
        if (processed) {
            return {
                status: 'skip',
                reason: 'Already processed'
            };
        }
        
        // Check freeze authority
        const isSafe = await checkTokenSafety(qnContext, mint);
        if (!isSafe) {
            return {
                status: 'skip',
                reason: 'Has freeze authority'
            };
        }
        
        // Check liquidity
        const quote = await getQuote(qnContext, WSOL_MINT, mint, 1000000000);
        if (!quote || quote.outAmount < MIN_LIQUIDITY_THRESHOLD) {
            return {
                status: 'skip',
                reason: 'Insufficient liquidity'
            };
        }
        
        // Generate swap transaction
        const swapTx = await generateSwap(qnContext, quote);
        if (!swapTx) {
            return {
                status: 'error',
                reason: 'Failed to generate swap'
            };
        }
        
        // Mark as processed
        await qnContext.kv.set(`processed_${mint}`, {
            timestamp: Date.now(),
            liquidity: quote.outAmount
        }, { ttl: 86400 }); // 24h TTL
        
        // Create limit order for take-profit
        const limitOrder = await createLimitOrder(
            qnContext, 
            mint, 
            quote.outAmount
        );
        
        return {
            status: 'success',
            mint,
            swapTransaction: swapTx,
            limitOrder: limitOrder?.order,
            outAmount: quote.outAmount
        };
        
    } catch (error) {
        console.error('Error processing pool:', error);
        return {
            status: 'error',
            error: error.message
        };
    }
}

async function checkTokenSafety(qnContext, mint) {
    try {
        const accountInfo = await qnContext.rpc.getAccountInfo(
            new PublicKey(mint),
            { encoding: 'jsonParsed' }
        );
        
        if (!accountInfo?.value?.data?.parsed) {
            return false;
        }
        
        const mintData = accountInfo.value.data.parsed.info;
        return !mintData.freezeAuthority;
        
    } catch (error) {
        console.error('Error checking token safety:', error);
        return false;
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

async function createLimitOrder(qnContext, mint, amount) {
    try {
        const takeProfitAmount = Math.floor(amount * 1.2); // 20% profit
        
        const response = await axios.post(
            `${qnContext.apiEndpoint}/limit-orders/create`,
            {
                maker: WALLET_ADDRESS,
                payer: WALLET_ADDRESS,
                inputMint: mint,
                outputMint: WSOL_MINT,
                params: {
                    makingAmount: amount.toString(),
                    takingAmount: takeProfitAmount.toString(),
                    expiredAt: Math.floor(Date.now() / 1000) + 86400
                }
            }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error creating limit order:', error);
        return null;
    }
}

module.exports = { main }; 