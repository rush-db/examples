import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import "./App.css";
import { db } from "./db";

// Form validation schema
const formSchema = z.object({
  // Personal Information
  firstName: z.string().min(2, "First name must be at least 2 characters"),
  lastName: z.string().min(2, "Last name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  phone: z.string().min(10, "Phone number must be at least 10 digits"),
  dateOfBirth: z.string().min(1, "Date of birth is required"),

  // Address Information
  address: z.object({
    street: z.string().min(5, "Street address is required"),
    city: z.string().min(2, "City is required"),
    state: z.string().min(2, "State is required"),
    zipCode: z.string().min(5, "ZIP code must be at least 5 characters"),
    country: z.string().min(2, "Country is required"),
  }),

  // Professional Information
  company: z.string().min(2, "Company name is required"),
  position: z.string().min(2, "Position is required"),
  experience: z.enum(["entry", "junior", "mid", "senior", "lead", "executive"]),
  salary: z.number().min(0, "Salary must be a positive number"),
  skills: z.array(z.string()).min(1, "At least one skill is required"),

  // Preferences
  preferences: z.object({
    newsletter: z.boolean(),
    notifications: z.boolean(),
    publicProfile: z.boolean(),
    dataSharing: z.boolean(),
  }),

  // Additional Information
  bio: z.string().max(500, "Bio must be less than 500 characters"),
  website: z.string().url("Invalid URL").optional().or(z.literal("")),
  linkedIn: z.string().url("Invalid LinkedIn URL").optional().or(z.literal("")),
  github: z.string().url("Invalid GitHub URL").optional().or(z.literal("")),
});

type FormData = z.infer<typeof formSchema>;

function App() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [submitMessage, setSubmitMessage] = useState("");

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      dateOfBirth: "",
      address: {
        street: "",
        city: "",
        state: "",
        zipCode: "",
        country: "US",
      },
      company: "",
      position: "",
      experience: "entry",
      salary: 0,
      skills: [],
      preferences: {
        newsletter: false,
        notifications: true,
        publicProfile: false,
        dataSharing: false,
      },
      bio: "",
      website: "",
      linkedIn: "",
      github: "",
    },
    mode: "onChange",
  });

  // Watch skills array for dynamic management
  const watchedSkills = watch("skills");

  const addSkill = (skill: string) => {
    if (skill.trim() && !watchedSkills.includes(skill.trim())) {
      setValue("skills", [...watchedSkills, skill.trim()], {
        shouldValidate: true,
      });
    }
  };

  const removeSkill = (index: number) => {
    setValue(
      "skills",
      watchedSkills.filter((_, i) => i !== index),
      { shouldValidate: true }
    );
  };

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setSubmitStatus("idle");
    setSubmitMessage("");

    try {
      // Prepare data for submission
      const formDataToSubmit = {
        ...data,
        submittedAt: new Date().toISOString(),
        userAgent: navigator.userAgent,
        formVersion: "1.0",
      };

      // Save to RushDB
      await db.records.createMany({
        label: "FORM_DATA",
        data: formDataToSubmit,
      });

      setSubmitStatus("success");
      setSubmitMessage("Form submitted successfully!");
      reset(); // Reset form after successful submission
    } catch (error) {
      console.error("Error submitting form:", error);
      setSubmitStatus("error");
      setSubmitMessage(
        error instanceof Error
          ? error.message
          : "Failed to submit form. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Mock data for testing
  const fillMockData = () => {
    const mockData: FormData = {
      firstName: "John",
      lastName: "Doe",
      email: "john.doe@example.com",
      phone: "+1 (555) 123-4567",
      dateOfBirth: "1990-05-15",
      address: {
        street: "123 Business Ave, Suite 100",
        city: "San Francisco",
        state: "CA",
        zipCode: "94105",
        country: "US",
      },
      company: "Tech Innovations Inc.",
      position: "Senior Software Engineer",
      experience: "senior",
      salary: 125000,
      skills: ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL"],
      preferences: {
        newsletter: true,
        notifications: true,
        publicProfile: false,
        dataSharing: false,
      },
      bio: "Experienced software engineer with a passion for building scalable web applications and leading development teams.",
      website: "https://johndoe.dev",
      linkedIn: "https://linkedin.com/in/johndoe",
      github: "https://github.com/johndoe",
    };

    // Reset form first, then set values
    reset(mockData);
  };

  return (
    <div className="app-container">
      <div className="form-header">
        <h1>Professional Registration Form</h1>
        <p>
          Complete business registration using React Hook Form + Zod + RushDB
        </p>
        <button
          type="button"
          onClick={fillMockData}
          className="mock-data-button"
        >
          Fill with Sample Data
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="complex-form">
        {/* Personal Information Section */}
        <section className="form-section">
          <h2>Personal Information</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="firstName">First Name *</label>
              <input
                id="firstName"
                placeholder="Enter your first name"
                {...register("firstName")}
                className={errors.firstName ? "error" : ""}
              />
              {errors.firstName && (
                <span className="error-message">
                  {errors.firstName.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="lastName">Last Name *</label>
              <input
                id="lastName"
                placeholder="Enter your last name"
                {...register("lastName")}
                className={errors.lastName ? "error" : ""}
              />
              {errors.lastName && (
                <span className="error-message">{errors.lastName.message}</span>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                id="email"
                type="email"
                placeholder="your.email@example.com"
                {...register("email")}
                className={errors.email ? "error" : ""}
              />
              {errors.email && (
                <span className="error-message">{errors.email.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone *</label>
              <input
                id="phone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                {...register("phone")}
                className={errors.phone ? "error" : ""}
              />
              {errors.phone && (
                <span className="error-message">{errors.phone.message}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="dateOfBirth">Date of Birth *</label>
            <input
              id="dateOfBirth"
              type="date"
              {...register("dateOfBirth")}
              className={errors.dateOfBirth ? "error" : ""}
            />
            {errors.dateOfBirth && (
              <span className="error-message">
                {errors.dateOfBirth.message}
              </span>
            )}
          </div>
        </section>

        {/* Address Information Section */}
        <section className="form-section">
          <h2>Address Information</h2>

          <div className="form-group">
            <label htmlFor="street">Street Address *</label>
            <input
              id="street"
              placeholder="123 Main Street, Apt 4B"
              {...register("address.street")}
              className={errors.address?.street ? "error" : ""}
            />
            {errors.address?.street && (
              <span className="error-message">
                {errors.address.street.message}
              </span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="city">City *</label>
              <input
                id="city"
                placeholder="San Francisco"
                {...register("address.city")}
                className={errors.address?.city ? "error" : ""}
              />
              {errors.address?.city && (
                <span className="error-message">
                  {errors.address.city.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="state">State *</label>
              <input
                id="state"
                {...register("address.state")}
                className={errors.address?.state ? "error" : ""}
              />
              {errors.address?.state && (
                <span className="error-message">
                  {errors.address.state.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="zipCode">ZIP Code *</label>
              <input
                id="zipCode"
                {...register("address.zipCode")}
                className={errors.address?.zipCode ? "error" : ""}
              />
              {errors.address?.zipCode && (
                <span className="error-message">
                  {errors.address.zipCode.message}
                </span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="country">Country *</label>
            <select
              id="country"
              {...register("address.country")}
              className={errors.address?.country ? "error" : ""}
            >
              <option value="US">United States</option>
              <option value="CA">Canada</option>
              <option value="UK">United Kingdom</option>
              <option value="AU">Australia</option>
              <option value="OTHER">Other</option>
            </select>
            {errors.address?.country && (
              <span className="error-message">
                {errors.address.country.message}
              </span>
            )}
          </div>
        </section>

        {/* Professional Information Section */}
        <section className="form-section">
          <h2>Professional Information</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="company">Company *</label>
              <input
                id="company"
                placeholder="e.g. Google, Microsoft, Startup Inc."
                {...register("company")}
                className={errors.company ? "error" : ""}
              />
              {errors.company && (
                <span className="error-message">{errors.company.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="position">Position *</label>
              <input
                id="position"
                placeholder="e.g. Software Engineer, Product Manager"
                {...register("position")}
                className={errors.position ? "error" : ""}
              />
              {errors.position && (
                <span className="error-message">{errors.position.message}</span>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="experience">Experience Level *</label>
              <select
                id="experience"
                {...register("experience")}
                className={errors.experience ? "error" : ""}
              >
                <option value="entry">Entry Level</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="executive">Executive</option>
              </select>
              {errors.experience && (
                <span className="error-message">
                  {errors.experience.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="salary">Annual Salary (USD) *</label>
              <input
                id="salary"
                type="number"
                min="0"
                step="1000"
                {...register("salary", { valueAsNumber: true })}
                className={errors.salary ? "error" : ""}
              />
              {errors.salary && (
                <span className="error-message">{errors.salary.message}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label>Skills *</label>
            <div className="skills-section">
              <div className="skills-input">
                <input
                  type="text"
                  placeholder="Add a skill and press Enter"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill(e.currentTarget.value);
                      e.currentTarget.value = "";
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={() => {
                    const input = document.querySelector(
                      ".skills-input input"
                    ) as HTMLInputElement;
                    addSkill(input.value);
                    input.value = "";
                  }}
                >
                  Add Skill
                </button>
              </div>
              <div className="skills-list">
                {watchedSkills.map((skill, index) => (
                  <span key={index} className="skill-tag">
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(index)}
                      className="remove-skill"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
            {errors.skills && (
              <span className="error-message">{errors.skills.message}</span>
            )}
          </div>
        </section>

        {/* Preferences Section */}
        <section className="form-section">
          <h2>Preferences</h2>

          <div className="checkbox-group">
            <label className="checkbox-label">
              <input type="checkbox" {...register("preferences.newsletter")} />
              Subscribe to newsletter
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                {...register("preferences.notifications")}
              />
              Enable notifications
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                {...register("preferences.publicProfile")}
              />
              Make profile public
            </label>

            <label className="checkbox-label">
              <input type="checkbox" {...register("preferences.dataSharing")} />
              Allow data sharing for research
            </label>
          </div>
        </section>

        {/* Additional Information Section */}
        <section className="form-section">
          <h2>Additional Information</h2>

          <div className="form-group">
            <label htmlFor="bio">Bio (max 500 characters)</label>
            <textarea
              id="bio"
              rows={4}
              {...register("bio")}
              className={errors.bio ? "error" : ""}
              placeholder="Tell us about yourself..."
            />
            {errors.bio && (
              <span className="error-message">{errors.bio.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="website">Website</label>
            <input
              id="website"
              type="url"
              {...register("website")}
              className={errors.website ? "error" : ""}
              placeholder="https://yourwebsite.com"
            />
            {errors.website && (
              <span className="error-message">{errors.website.message}</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="linkedIn">LinkedIn</label>
              <input
                id="linkedIn"
                type="url"
                {...register("linkedIn")}
                className={errors.linkedIn ? "error" : ""}
                placeholder="https://linkedin.com/in/username"
              />
              {errors.linkedIn && (
                <span className="error-message">{errors.linkedIn.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="github">GitHub</label>
              <input
                id="github"
                type="url"
                {...register("github")}
                className={errors.github ? "error" : ""}
                placeholder="https://github.com/username"
              />
              {errors.github && (
                <span className="error-message">{errors.github.message}</span>
              )}
            </div>
          </div>
        </section>

        {/* Submit Section */}
        <section className="form-section">
          <div className="submit-section">
            <div className="form-status">
              {submitStatus === "success" && (
                <div className="success-message">{submitMessage}</div>
              )}
              {submitStatus === "error" && (
                <div className="error-message">{submitMessage}</div>
              )}
            </div>

            <div className="submit-buttons">
              <button
                type="button"
                onClick={() => reset()}
                className="reset-button"
                disabled={isSubmitting}
              >
                Reset Form
              </button>
              <button
                type="submit"
                className={`submit-button ${isSubmitting ? "loading" : ""}`}
                disabled={!isValid || isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <span>Submitting</span>
                    <span className="loading-dots">...</span>
                  </>
                ) : (
                  "Submit to RushDB"
                )}
              </button>
            </div>
          </div>
        </section>
      </form>
    </div>
  );
}

export default App;
