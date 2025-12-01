from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])

@router.get("/payment-success", response_class=HTMLResponse)
async def payment_success_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Successful</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center">
            <div class="mb-6">
                <div class="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-green-100">
                    <i class="fas fa-check text-4xl text-green-600"></i>
                </div>
            </div>
            
            <h2 class="text-3xl font-extrabold text-gray-900 mb-2">Payment Successful!</h2>
            <p class="text-gray-500 mb-8">
                Thank you for your purchase. Your ticket has been confirmed and sent to your email.
            </p>

            <div class="space-y-4">
                <a href="/docs" class="block w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200">
                    View My Tickets (API)
                </a>
                <a href="/" class="block w-full bg-white border border-gray-300 text-gray-700 font-semibold py-3 px-4 rounded-lg hover:bg-gray-50 transition duration-200">
                    Go to Homepage
                </a>
            </div>
            
            <p class="mt-8 text-xs text-gray-400">
                Transaction ID: Confirmed via Stripe
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/payment-cancel", response_class=HTMLResponse)
async def payment_cancel_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Cancelled</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center">
            <div class="mb-6">
                <div class="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-red-100">
                    <i class="fas fa-times text-4xl text-red-600"></i>
                </div>
            </div>
            
            <h2 class="text-3xl font-extrabold text-gray-900 mb-2">Payment Cancelled</h2>
            <p class="text-gray-500 mb-8">
                You cancelled the checkout process. No charges were made.
            </p>

            <div class="space-y-4">
                <a href="/docs" class="block w-full bg-gray-800 hover:bg-gray-900 text-white font-semibold py-3 px-4 rounded-lg transition duration-200">
                    Try Again
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)