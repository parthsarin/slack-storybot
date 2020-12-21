import React, { FunctionComponent, useState } from 'react';
import { Container } from 'react-bootstrap';
import './App.css';
import Authenticate from './Authenticate';
import WriteStory from './WriteStory';

interface User {
    username: string,
    profile_image?: string,
    first_name: string,
    last_name: string,
    slack_id?: string,
}

const App: FunctionComponent<{}> = () => {
    // Get the slack user from local storage if it exists there
    const storedUser = localStorage.getItem("slackUser");
    const [slackUser, setSlackUser] = useState<User | null>(
        storedUser ? JSON.parse(storedUser) : null
    );

    if (!slackUser) {
        // Not authenticated yet
        return (
            <Authenticate
                onSubmit={
                    (newUser) => {
                        setSlackUser(newUser);
                        localStorage.setItem(
                            'slackUser', 
                            JSON.stringify(newUser)
                        );
                    }
                }
                newUser={localStorage.getItem('slackUser') === null}
            />
        );
    }

    // Authenticated
    return (
        <Container className="mt-2 mb-2">
            <div className="text-center header">
                <h1>Hey, {slackUser.first_name}!</h1>
                <p>
                    Not you?&nbsp;
                    <button 
                        className="link-button" 
                        onClick={() => setSlackUser(null)}>
                        Re-authenticate here
                    </button>.
                </p>
            </div>
            <WriteStory
                user={slackUser}
            />
        </Container>
    );
}

export default App;
export type { User };