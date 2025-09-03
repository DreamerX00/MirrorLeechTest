#!/usr/bin/env python3
# Auth Bot - utils/url_shortener.py

import aiohttp
import logging
import random
from typing import Optional, Dict, Any

from auth_bot import URL_SHORTENER_API, URL_SHORTENER_API_KEY, URL_SHORTENER_DOMAIN, URL_SHORTENER_SECURE, shorteners_list

logger = logging.getLogger(__name__)

async def shorten_url(long_url: str) -> Optional[str]:
    """
    Shorten a URL using the configured URL shortener service.
    
    Args:
        long_url: The original long URL to shorten
        
    Returns:
        The shortened URL if successful, None otherwise
    """
    # Check if we have shorteners in the list
    if shorteners_list:
        # Randomly select a shortener from the list
        shortener = random.choice(shorteners_list)
        api = shortener['api']
        key = shortener['key']
        domain = shortener.get('domain')
        secure = shortener.get('secure', True)
        
        logger.info(f"Using randomly selected shortener: {api}")
        
        try:
            # TinyURL API
            if "tinyurl" in api.lower():
                return await _shorten_with_tinyurl(long_url, key, domain, secure)
            
            # Bitly API
            elif "bitly" in api.lower():
                return await _shorten_with_bitly(long_url, key, domain, secure)
            
            # Rebrandly API
            elif "rebrandly" in api.lower():
                return await _shorten_with_rebrandly(long_url, key, domain, secure)
            
            # Cuttly API
            elif "cuttly" in api.lower():
                return await _shorten_with_cuttly(long_url, key, domain, secure)
            
            # Default to TinyURL if service not recognized
            else:
                logger.warning(f"Unrecognized URL shortener service: {api}. Using TinyURL as fallback.")
                return await _shorten_with_tinyurl(long_url, key, domain, secure)
        except Exception as e:
            logger.error(f"Error with shortener {api}: {e}. Trying fallback.")
    
    # Fallback to environment variables if no shorteners in list or if the selected one failed
    if URL_SHORTENER_API and URL_SHORTENER_API_KEY:
        logger.info("Using environment variables for URL shortening")
        try:
            # TinyURL API
            if "tinyurl" in URL_SHORTENER_API.lower():
                return await _shorten_with_tinyurl(long_url)
            
            # Bitly API
            elif "bitly" in URL_SHORTENER_API.lower():
                return await _shorten_with_bitly(long_url)
            
            # Rebrandly API
            elif "rebrandly" in URL_SHORTENER_API.lower():
                return await _shorten_with_rebrandly(long_url)
            
            # Cuttly API
            elif "cuttly" in URL_SHORTENER_API.lower():
                return await _shorten_with_cuttly(long_url)
            
            # Default to TinyURL if service not recognized
            else:
                logger.warning(f"Unrecognized URL shortener service: {URL_SHORTENER_API}. Using TinyURL as fallback.")
                return await _shorten_with_tinyurl(long_url)
        except Exception as e:
            logger.error(f"Error shortening URL with environment variables: {e}")
            return None
    else:
        logger.info("URL shortener not configured, returning original URL")
        return None

async def _shorten_with_tinyurl(long_url: str, api_key: str = None, domain: str = None, secure: bool = True) -> Optional[str]:
    """
    Shorten a URL using the TinyURL API.
    
    Args:
        long_url: The original long URL to shorten
        api_key: The API key to use (defaults to environment variable)
        domain: The custom domain to use (defaults to environment variable)
        secure: Whether to use secure settings
        
    Returns:
        The shortened URL if successful, None otherwise
    """
    api_url = f"https://api.tinyurl.com/create"
    
    # Use provided API key or fall back to environment variable
    key = api_key if api_key else URL_SHORTENER_API_KEY
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    # Use custom domain if provided, otherwise use default
    custom_domain = domain if domain else URL_SHORTENER_DOMAIN
    final_domain = custom_domain if custom_domain else "tiny.one"
    
    payload = {
        "url": long_url,
        "domain": final_domain,
        "is_private": secure  # For enhanced security
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", {}).get("tiny_url")
            else:
                logger.error(f"TinyURL API error: {response.status} - {await response.text()}")
                return None

async def _shorten_with_bitly(long_url: str, api_key: str = None, domain: str = None, secure: bool = True) -> Optional[str]:
    """
    Shorten a URL using the Bitly API.
    
    Args:
        long_url: The original long URL to shorten
        api_key: The API key to use (defaults to environment variable)
        domain: The custom domain to use (defaults to environment variable)
        secure: Whether to use secure settings (not used for Bitly)
        
    Returns:
        The shortened URL if successful, None otherwise
    """
    api_url = "https://api-ssl.bitly.com/v4/shorten"
    
    # Use provided API key or fall back to environment variable
    key = api_key if api_key else URL_SHORTENER_API_KEY
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "long_url": long_url
    }
    
    # Add custom domain if provided
    custom_domain = domain if domain else URL_SHORTENER_DOMAIN
    if custom_domain:
        payload["domain"] = custom_domain
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("link")
            else:
                logger.error(f"Bitly API error: {response.status} - {await response.text()}")
                return None

async def _shorten_with_rebrandly(long_url: str, api_key: str = None, domain: str = None, secure: bool = True) -> Optional[str]:
    """
    Shorten a URL using the Rebrandly API.
    
    Args:
        long_url: The original long URL to shorten
        api_key: The API key to use (defaults to environment variable)
        domain: The custom domain to use (defaults to environment variable)
        secure: Whether to use HTTPS for the shortened URL
        
    Returns:
        The shortened URL if successful, None otherwise
    """
    api_url = "https://api.rebrandly.com/v1/links"
    
    # Use provided API key or fall back to environment variable
    key = api_key if api_key else URL_SHORTENER_API_KEY
    
    headers = {
        "apikey": key,
        "Content-Type": "application/json"
    }
    
    # Use custom domain if provided, otherwise use default
    custom_domain = domain if domain else URL_SHORTENER_DOMAIN
    domain_name = custom_domain if custom_domain else "rebrand.ly"
    
    # Use provided secure setting or fall back to environment variable
    use_https = secure if secure is not None else URL_SHORTENER_SECURE
    
    payload = {
        "destination": long_url,
        "domain": {"fullName": domain_name},
        "https": use_https  # Use HTTPS based on configuration
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return f"https://{data.get('shortUrl')}" if data.get('shortUrl') else None
            else:
                logger.error(f"Rebrandly API error: {response.status} - {await response.text()}")
                return None

async def _shorten_with_cuttly(long_url: str, api_key: str = None, domain: str = None, secure: bool = True) -> Optional[str]:
    """
    Shorten a URL using the Cuttly API.
    
    Args:
        long_url: The original long URL to shorten
        api_key: The API key to use (defaults to environment variable)
        domain: The custom domain to use (not used for Cuttly)
        secure: Whether to use HTTPS for the shortened URL
        
    Returns:
        The shortened URL if successful, None otherwise
    """
    # Use provided API key or fall back to environment variable
    key = api_key if api_key else URL_SHORTENER_API_KEY
    
    api_url = f"https://cutt.ly/api/api.php?key={key}&short={long_url}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("url", {}).get("status") == 7:  # 7 means success
                    short_link = data.get("url", {}).get("shortLink")
                    
                    # Ensure HTTPS if configured
                    use_https = secure if secure is not None else URL_SHORTENER_SECURE
                    if use_https and short_link and short_link.startswith("http://"):
                        short_link = short_link.replace("http://", "https://")
                    
                    return short_link
                else:
                    logger.error(f"Cuttly API error: {data.get('url', {}).get('status')}")
                    return None
            else:
                logger.error(f"Cuttly API error: {response.status} - {await response.text()}")
                return None