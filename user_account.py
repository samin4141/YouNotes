import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


from fastapi import FastAPI, Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import nest_asyncio
nest_asyncio.apply()

app = FastAPI()

# Load Google API Credentials
CLIENT_SECRETS_FILE = "client_secret_1082790366670-snt3k1uk3s7mtk99em87qselqm3b3e3r.apps.googleusercontent.com.json"
SCOPES = ["openid",
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/youtube.readonly"]

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri="http://localhost:5000/callback"
)

@app.get("/")
def home():
    return {"message": "Go to /login to authenticate"}

# Step 1: Redirect User to Google OAuth
@app.get("/login")
def login():
    auth_url, _ = flow.authorization_url(prompt="consent")
    return {"auth_url": auth_url}

# Step 2: Handle Google OAuth Callback
@app.get("/callback")
def callback(request: Request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri="http://localhost:5000/callback"
    )
    
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    youtube = build("youtube", "v3", credentials=credentials)
    oauth2 = build("oauth2", "v2", credentials=credentials)

    # ✅ Get User's Gmail
    try:
        user_info = oauth2.userinfo().get().execute()
        user_email = user_info.get("email", "Unknown Email")
    except Exception as e:
        user_email = f"Error retrieving email: {str(e)}"

    # ✅ Fetch Liked Videos
    try:
        liked_videos_response = youtube.playlistItems().list(
            part="snippet",
            playlistId="LL",  # Liked Videos Playlist
            maxResults=10
        ).execute()

        liked_videos = [
            {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            }
            for item in liked_videos_response.get("items", [])
        ]
    except Exception as e:
        liked_videos = [f"Error retrieving liked videos: {str(e)}"]

    # ✅ Fetch User's Playlists
    try:
        playlists_response = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=10
        ).execute()

        playlists = [
            {
                "title": item["snippet"]["title"],
                "id": item["id"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            }
            for item in playlists_response.get("items", [])
        ]
    except Exception as e:
        playlists = [f"Error retrieving playlists: {str(e)}"]

    return {
        "email": user_email,
        "liked_videos": liked_videos,
        "playlists": playlists
    }


# Run the FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
